# Project Instructions

## Frontend priority

Frontend quality is a critical requirement of this project.

Never generate a frontend merely to make functionality work.

Every interface must be treated as production-quality UI/UX.

Before modifying or creating any frontend screen:

1. Understand the purpose of the screen.
2. Identify the user who will use it.
3. Review the existing design system.
4. Review existing components before creating new ones.
5. Maintain visual consistency with the rest of the application.
6. Consider desktop, tablet and mobile behavior.
7. Implement the interface.
8. Run the application and visually inspect the result.
9. Correct visual inconsistencies before considering the task finished.

## Design consistency

Always reuse the project's existing:

* Colors
* Typography
* Spacing system
* Border radii
* Shadows
* Buttons
* Inputs
* Cards
* Modals
* Navigation
* Icons
* Layout patterns

Do not introduce a new visual style without an explicit reason.

Never create multiple slightly different versions of the same component.

Prefer reusable components.

## Avoid generic AI interfaces

Do not create interfaces that look obviously AI-generated.

Avoid:

* Random gradients
* Excessive purple/blue gradients
* Excessive rounded cards
* Cards inside cards without purpose
* Giant headings without hierarchy
* Random shadows
* Excessive glassmorphism
* Unnecessary decorative elements
* Random icons
* Inconsistent spacing
* Excessive empty space
* Centering everything
* Repetitive dashboard layouts
* Placeholder-looking UI

Every visual decision must have a reason connected to usability or the project's visual identity.

## Layout

Maintain a clear hierarchy:

Page
→ Sections
→ Components
→ Content

Spacing must be systematic rather than arbitrary.

Elements that belong together must appear visually grouped.

Different sections must have enough separation to be understood immediately.

Do not fill every available area with cards.

## Responsive behavior

Every frontend implementation must support:

* Desktop
* Tablet
* Mobile

Never solve responsive problems by simply hiding important content.

Consider:

* Navigation transformation
* Column stacking
* Typography scaling
* Touch targets
* Tables on small screens
* Modal dimensions
* Form layouts
* Overflow
* Long text

## Components

Before creating a new component, search the existing codebase.

If an equivalent component exists, reuse or extend it.

Components should be:

* Reusable
* Predictable
* Accessible
* Easy to maintain
* Visually consistent

Avoid creating abstractions for components that are only used once unless there is a clear architectural benefit.

## UX

Never prioritize aesthetics over usability.

Interfaces must clearly communicate:

* What the user can do
* What is currently happening
* What succeeded
* What failed
* What requires attention

All important actions need appropriate:

* Loading states
* Empty states
* Error states
* Success states
* Disabled states

## Forms

Forms must have:

* Visible labels
* Helpful validation
* Clear error messages
* Correct input types
* Logical grouping
* Consistent spacing
* Clear primary action
* Appropriate disabled/loading states

Do not rely only on placeholder text as a label.

## Accessibility

Use semantic HTML whenever possible.

Maintain sufficient contrast.

All interactive elements must be keyboard accessible.

Buttons must be actual buttons when appropriate.

Inputs must have labels.

Images must have appropriate alternative text.

## Existing design

Existing approved screens and components are the primary source of truth.

When creating a new screen:

1. Search for similar existing screens.
2. Identify their design patterns.
3. Reuse those patterns.
4. Extend them only when necessary.

Do not redesign existing patterns without explicit instruction.

## Verification

A frontend task is NOT complete merely because:

* It compiles
* There are no TypeScript errors
* Tests pass
* The requested functionality exists

Frontend work is complete only after verifying the rendered interface.

When browser tools are available:

1. Start the application.
2. Open the affected screen.
3. Inspect the result.
4. Test relevant interactions.
5. Check mobile and desktop layouts.
6. Fix visual or usability problems found during inspection.

## Project documentation

Before significant frontend work, consult when available:

* `docs/DESIGN_SYSTEM.md`
* `docs/FRONTEND_RULES.md`
* `docs/UI_EXAMPLES.md`
* `.claude/skills/frontend-project/SKILL.md`

When a frontend mistake is corrected and is likely to happen again, document the lesson so the same mistake is not repeated.
