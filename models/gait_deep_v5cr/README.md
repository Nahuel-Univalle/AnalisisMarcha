# V5-CR: frozen deployment package

Selected checkpoint: `gait_deep_v5exp_V5CR_7e9ed60965fe.pt`.

SHA-256: `7e9ed60965feabe85a3dc2e6ddc568265596c706a378a94d7fdf01b6a8c9dade`.

The weights and label map are exact copies of the original research files in
`docs/optimizacion_final_v5_2026-11-19/checkpoints/`. The only metadata corrections
are `feature_scaler.columns` (the 33 names recorded in the training bank and
configuration) and `config.status` (V5-CR identification). All median, mean and
standard deviation values are unchanged. See `deployment_manifest.json`.

Production predictor: `scripts/video_training/deep/15_predict_deep_video_v5cr.py`.
Preprocessing is vendored in its `v5cr/` directory; only import bootstrap paths
were adapted. No runtime dependency on the research directory is required.

Protocol: sequential normalized pose extraction at 15 FPS and maximum dimension
720 pixels; original cap of 400 sampled frames; first pose anchor, effective
analysis span up to 5.03 s; 2.6 s windows/40 samples, stride 0.4 s; reject windows
with fewer than 20 valid torso poses; select up to 5 accepted windows using
unique rounded linspace indices; 68 sequence channels plus 33 tabular values;
original median imputation and standardization; mean float32 window logits,
then temperature 0.6615 and softmax. Aspect correction and hip-relative
interpolation match V5-CR training. PyTorch uses two CPU intra-op threads.

Missing/altered artifacts fail closed. No automatic fallback is performed.
`GAIT_MODEL_VERSION=v4` explicitly selects the preserved V4 backup for both
inference and administrative metadata; otherwise V5-CR is selected.

Internal validation only: accuracy 0.8598; macro F1 0.7852, using the same 117
videos/67 subject groups used during model development. These figures do not
establish clinical or external validity. Motion robustness tests cover specific
coordinate transformations, not arbitrary camera motion or real-world safety.

Reproduction (does not train):

```powershell
.venv311/Scripts/python.exe scripts/video_training/deep/prepare_v5cr_deployment.py
npm run test:deep
npm run test:v5cr:presentation
```

The packaging script requires the existing research bank to verify feature
order. Do not run any training scripts to deploy this package. The full evidence,
isolated database test instructions and remaining limitations are recorded in
`docs/integracion_v5cr_2026-11-19/INFORME_FINAL_INTEGRACION.md`.
