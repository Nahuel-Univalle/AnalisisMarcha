from math import atan2, degrees


def landmark_point(landmarks, landmark_enum, name):
    landmark = landmarks[landmark_enum[name].value]
    return {
        "x": float(landmark.x),
        "y": float(landmark.y),
        "z": float(getattr(landmark, "z", 0.0)),
        "visibility": float(getattr(landmark, "visibility", 0.0)),
    }


def point_visibility(*points):
    if not points:
        return 0.0
    return sum(point["visibility"] for point in points) / len(points)


def distance_x(left, right):
    return abs(left["x"] - right["x"])


def center(left, right):
    return {
        "x": (left["x"] + right["x"]) / 2,
        "y": (left["y"] + right["y"]) / 2,
    }


def trunk_angle_degrees(shoulder_center, hip_center):
    dx = shoulder_center["x"] - hip_center["x"]
    dy = hip_center["y"] - shoulder_center["y"]
    if dy == 0:
        return 0.0
    return abs(degrees(atan2(dx, dy)))


def extract_pose_series(video_path, cv2, mp, np, max_frames=240):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_seconds = frame_count / fps if fps > 0 else 0.0
    stride = max(1, frame_count // max_frames) if frame_count > max_frames else 1

    pose_module = mp.solutions.pose
    landmark_enum = pose_module.PoseLandmark

    frames_analyzed = 0
    frames_with_pose = 0
    ankle_distances = []
    hip_centers = []
    shoulder_centers = []
    trunk_angles = []
    left_wrist_offsets = []
    right_wrist_offsets = []

    with pose_module.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        frame_index = 0
        while cap.isOpened() and frames_analyzed < max_frames:
            ok, frame = cap.read()
            if not ok:
                break

            if frame_index % stride != 0:
                frame_index += 1
                continue

            frames_analyzed += 1
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                left_ankle = landmark_point(landmarks, landmark_enum, "LEFT_ANKLE")
                right_ankle = landmark_point(landmarks, landmark_enum, "RIGHT_ANKLE")
                left_hip = landmark_point(landmarks, landmark_enum, "LEFT_HIP")
                right_hip = landmark_point(landmarks, landmark_enum, "RIGHT_HIP")
                left_shoulder = landmark_point(
                    landmarks, landmark_enum, "LEFT_SHOULDER"
                )
                right_shoulder = landmark_point(
                    landmarks, landmark_enum, "RIGHT_SHOULDER"
                )
                left_wrist = landmark_point(landmarks, landmark_enum, "LEFT_WRIST")
                right_wrist = landmark_point(landmarks, landmark_enum, "RIGHT_WRIST")

                core_visibility = point_visibility(
                    left_ankle,
                    right_ankle,
                    left_hip,
                    right_hip,
                    left_shoulder,
                    right_shoulder,
                )

                if core_visibility >= 0.35:
                    frames_with_pose += 1
                    hip_center = center(left_hip, right_hip)
                    shoulder_center = center(left_shoulder, right_shoulder)
                    hip_centers.append(hip_center)
                    shoulder_centers.append(shoulder_center)
                    ankle_distances.append(distance_x(left_ankle, right_ankle))
                    trunk_angles.append(
                        trunk_angle_degrees(shoulder_center, hip_center)
                    )
                    left_wrist_offsets.append(left_wrist["x"] - left_shoulder["x"])
                    right_wrist_offsets.append(
                        right_wrist["x"] - right_shoulder["x"]
                    )

            frame_index += 1

    cap.release()

    return {
        "fps": fps,
        "frame_count": frame_count,
        "duration_seconds": duration_seconds,
        "frames_analyzed": frames_analyzed,
        "frames_with_pose": frames_with_pose,
        "ankle_distances": np.array(ankle_distances, dtype=float),
        "hip_centers": hip_centers,
        "shoulder_centers": shoulder_centers,
        "trunk_angles": np.array(trunk_angles, dtype=float),
        "left_wrist_offsets": np.array(left_wrist_offsets, dtype=float),
        "right_wrist_offsets": np.array(right_wrist_offsets, dtype=float),
    }
