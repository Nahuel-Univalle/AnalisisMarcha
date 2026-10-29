---

name: frontend-project
description: Design and implement production-quality frontend interfaces for this project. Use this skill whenever creating, modifying, reviewing or correcting pages, components, layouts, forms, dashboards, navigation or any other user interface.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Frontend Project Skill

## Objective

Act as both a senior frontend engineer and UI/UX designer for this project.

The goal is not merely to implement functionality.

The goal is to produce interfaces that are:

* Visually polished
* Consistent
* Responsive
* Accessible
* Easy to understand
* Appropriate for the product
* Production-ready

## Required workflow

For every frontend task:

### 1. Investigate

Before writing code:

* Inspect the existing page.
* Inspect related components.
* Inspect the design system.
* Look for reusable patterns.
* Understand the user and purpose of the feature.

Never start designing blindly.

### 2. Establish the visual direction

Determine:

* Information hierarchy
* Layout
* Spacing
* Typography
* Component hierarchy
* Interaction states
* Responsive behavior

Do this before implementation.

### 3. Reuse before creating

Search the codebase for existing:

* Buttons
* Inputs
* Cards
* Tables
* Modals
* Dropdowns
* Navigation
* Badges
* Alerts
* Empty states
* Loading components

Reuse the project's components whenever possible.

### 4. Implement

Create maintainable frontend code that follows the project's architecture and conventions.

Avoid unnecessary abstractions and dependencies.

### 5. Visually verify

After implementation, inspect the rendered application.

Check:

* Alignment
* Spacing
* Typography
* Hierarchy
* Colors
* Overflow
* Responsive behavior
* Empty states
* Error states
* Loading states
* Interaction feedback

Do not declare completion until visual verification has been performed when browser access is available.

## Design quality principles

### Hierarchy

The user should understand the screen within seconds.

Primary information must dominate secondary information.

Primary actions must be obvious.

Secondary actions should not compete visually with primary actions.

### Spacing

Use consistent spacing rather than arbitrary pixel values.

Related elements should be close.

Unrelated sections should have stronger separation.

### Color

Use the project's established palette.

Color should communicate meaning rather than merely decorate the interface.

Avoid introducing unnecessary accent colors.

### Typography

Use typography to establish hierarchy.

Do not rely exclusively on font size.

Use:

* Weight
* Size
* Line height
* Contrast
* Spacing

as a coordinated system.

### Cards

Do not automatically wrap every piece of information in a card.

Cards should represent meaningful groups or independent objects.

Avoid nested cards unless the information hierarchy requires them.

### Motion

Animations should communicate:

* State transitions
* Hierarchy
* Feedback
* Spatial relationships

Do not add animation purely because it looks impressive.

Prefer subtle purposeful motion.

## AI design anti-patterns

Never default to:

* Purple gradients
* Blue-purple SaaS themes
* Glassmorphism everywhere
* Excessive pill-shaped components
* Excessively rounded corners
* Floating cards without hierarchy
* Huge hero typography for normal application screens
* Decorative charts with meaningless data
* Arbitrary icons
* Generic dashboards
* Random gradients
* Random shadows
* Excessive animations

The result should feel intentionally designed for this product.

## Learning from corrections

When the user rejects a visual implementation:

1. Identify exactly what was wrong.
2. Determine the underlying design rule.
3. Correct the implementation.
4. Add the reusable lesson to the project's frontend knowledge when appropriate.

Do not simply fix the isolated component if the same mistake could occur elsewhere.

## References

When available, consult:

* `docs/DESIGN_SYSTEM.md`
* `docs/FRONTEND_RULES.md`
* `docs/UI_EXAMPLES.md`
* `.claude/skills/frontend-project/references/components.md`
* `.claude/skills/frontend-project/references/pages.md`
* `.claude/skills/frontend-project/references/mistakes.md`

Existing approved application screens are the strongest visual reference.
