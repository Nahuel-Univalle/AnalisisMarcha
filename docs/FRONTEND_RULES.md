# Project Design System

This document defines the visual rules of the project.

Claude must follow these rules when creating or modifying frontend interfaces.

If an existing approved component or screen conflicts with this document,
the approved existing implementation should be analyzed before making changes.

---

# 1. General Design Principles

The interface should feel:

- Professional
- Modern
- Clean
- Consistent
- Easy to understand
- Functional rather than decorative

Avoid unnecessary visual complexity.

Do not create decorative UI elements that do not improve usability.

---

# 2. Colors

Use the colors already defined in the project whenever possible.

Before introducing a new color:

1. Search the existing CSS, Tailwind configuration, theme or design tokens.
2. Verify whether an equivalent color already exists.
3. Reuse existing colors instead of creating new ones.

Color should communicate meaning.

Typical semantic usage:

- Primary: main actions
- Secondary: secondary actions
- Success: successful states
- Warning: warnings
- Danger: destructive actions and errors
- Neutral: backgrounds, borders and secondary text

Never introduce random gradients.

Never introduce a new accent color without justification.

---

# 3. Typography

Use the typography already configured in the project.

Maintain a clear hierarchy.

Recommended hierarchy:

Page title:
- Most visually important text on the page
- Usually one per page

Section title:
- Used to separate major content areas

Subsection title:
- Used inside complex sections

Body:
- Normal application content

Secondary text:
- Descriptions, metadata and supporting information

Avoid:

- Excessively large headings
- Too many font sizes
- Arbitrary font weights
- Very small text

---

# 4. Spacing

Spacing must be systematic.

Prefer consistent values such as:

4px
8px
12px
16px
24px
32px
48px
64px

Do not use arbitrary values unless necessary.

Related elements should have less spacing.

Different sections should have greater spacing.

---

# 5. Border Radius

Use the existing border radius system.

Do not make every element extremely rounded.

Suggested hierarchy:

Small elements:
6px - 8px

Inputs and buttons:
8px - 10px

Cards:
10px - 14px

Large containers:
maximum 16px unless the design explicitly requires otherwise.

Avoid excessive pill-shaped elements.

---

# 6. Shadows

Use shadows carefully.

Shadows should indicate:

- elevation
- overlays
- floating elements
- dialogs
- dropdowns

Do not apply large shadows to every card.

Prefer borders or subtle backgrounds for normal content containers.

---

# 7. Buttons

Buttons should have clear hierarchy.

Primary button:
Used for the most important action.

Secondary button:
Used for alternative actions.

Ghost/text button:
Used for low-priority actions.

Danger button:
Used for destructive actions.

Every button should support when applicable:

- default
- hover
- active
- focus
- disabled
- loading

Do not place multiple visually dominant buttons next to each other unless necessary.

---

# 8. Inputs

Inputs must:

- Have visible labels
- Display validation messages clearly
- Maintain consistent heights
- Use consistent spacing
- Show focus state
- Show error state
- Show disabled state

Placeholder text must not replace the label.

---

# 9. Cards

Cards must represent meaningful groups of information.

Do not place every section inside a card.

Avoid cards inside cards unless the hierarchy genuinely requires it.

Cards should normally contain:

- related content
- a clear information group
- an independent entity
- a relevant action group

---

# 10. Tables

Tables should prioritize readability.

Use:

- clear headers
- adequate spacing
- predictable column alignment
- responsive behavior
- empty states
- loading states

Actions should normally appear at the end of each row.

On mobile, evaluate whether the table should:

- scroll horizontally
- transform into another layout
- show only essential information

Do not simply hide important information.

---

# 11. Icons

Use the project's existing icon library.

Do not mix multiple icon libraries unnecessarily.

Icons must have a purpose.

Do not add decorative icons to every title, card or button.

---

# 12. Responsive Design

All screens must be tested conceptually for:

Desktop
Tablet
Mobile

Desktop should not simply be a stretched mobile interface.

Mobile should not simply be a compressed desktop interface.

Adapt:

- navigation
- columns
- forms
- tables
- action placement
- typography
- spacing
- dialogs

---

# 13. Accessibility

Maintain adequate contrast.

Interactive elements must show focus.

Use semantic HTML.

Use actual buttons for actions.

Use actual links for navigation.

Inputs must have associated labels.

Important information should not depend exclusively on color.