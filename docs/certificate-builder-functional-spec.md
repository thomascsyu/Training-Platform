# Certificate Builder — Functional Specification

| Field | Value |
|-------|-------|
| Feature | Certificate Builder |
| Audience | Product, design, engineering |
| Status | Draft for implementation |
| Actors | Admin only |
| Related surfaces | `/admin/certificates` (Issued + Templates tabs), `certificate_templates` collection, `/certificates/preview` |

---

## 1. Purpose

Give admins a guided flow to **review and create a certificate configuration for a specific course**: choose or name a template, set visual layout and wording, preview the result in real time, then save the configuration so issued certificates for that course use it.

This feature extends the existing global certificate template system (`certificate_templates`, Admin Certificates → Templates tab) with **course association**, **custom background upload**, **orientation**, **admin-authored body text with placeholders**, and an explicit **Configure → Review → Save** builder flow.

---

## 2. Goals and Non-Goals

### Goals

- Link a certificate configuration to one existing course.
- Let the admin select an existing template or create a new uniquely named template.
- Support custom background image upload (including drag-and-drop).
- Support Landscape (default) and Portrait orientation.
- Let the admin define certificate wording with variable placeholders.
- Show a live preview used as the Review step before save.
- Persist the configuration so future issuances for that course resolve to this template.

### Non-Goals (this iteration)

- Student-facing builder or self-serve certificate design.
- Multi-course bulk assignment of one template in the builder UI (API may still support global/default templates).
- Free-form WYSIWYG HTML/CSS editing beyond the body text field (existing HTML templates remain for advanced cases outside this builder).
- Changing quiz auto-issue rules, ID format, or email delivery (covered by existing certificate settings).
- Version history / rollback of templates.

---

## 3. Current System Baseline

| Capability | Today | Builder gap |
|------------|--------|-------------|
| Named templates with colors + preset artwork | Yes (`certificate_templates`) | No course binding |
| Background | Preset keys: `plain`, `geometric`, `waves`, `guilloche`, `corners` | No custom image upload |
| Orientation | Hardcoded landscape `11in × 8.5in` | No portrait toggle |
| Body copy | Fixed layout + i18n strings; optional raw HTML | No admin wording field with placeholders |
| Preview | `POST /certificates/preview` (admin certificates page) | Not wired as a builder Review step |
| Course styling | `apply_to_course` on customize updates existing certs | No first-class course ↔ template config |

The builder should **reuse** template CRUD, placeholder rendering (`{{user_name}}`, etc.), PDF generation, and preview endpoints where possible, and **add** the fields/flows below.

---

## 4. Personas and Access

| Role | Access |
|------|--------|
| Admin | Full create / edit / review / save |
| Client manager | No builder access (read-only certificates as today) |
| Student | Receives issued certificates only |

All builder APIs and UI routes require `admin`.

---

## 5. User Flow

```
Admin opens Certificate Builder (from course detail or Admin → Certificates / Templates)
        │
        ▼
┌───────────────────┐
│ 1. Configure      │  Course · Template name · Background · Orientation · Body text
└─────────┬─────────┘
          │ live preview updates as fields change
          ▼
┌───────────────────┐
│ 2. Review         │  Full-size preview: alignment, readability, image quality
└─────────┬─────────┘
          │ Confirm → Save
          ▼
┌───────────────────┐
│ 3. Saved          │  Template stored; course linked; toast + return to list / course
└───────────────────┘
```

### Entry points

1. **From a course** — “Certificate” / “Certificate Builder” on admin course management → course pre-selected.
2. **From Admin Certificates → Templates** — “Create with Builder” → course required before save.
3. **Edit existing** — open an existing course-linked template → same flow in edit mode.

### Exit / cancel

- Cancel or close discards unsaved changes (confirm if dirty).
- Uploaded background images that were never saved may be orphaned; cleanup is out of scope for v1 (document as follow-up).

---

## 6. Functional Requirements

### 6.1 Course association

| ID | Requirement |
|----|-------------|
| CB-01 | Admin must select exactly one existing course before save. |
| CB-02 | Course picker lists existing courses (include private), searchable by title. |
| CB-03 | When opened from a course context, `course_id` is pre-filled and shown as read-only (or with an explicit “Change course” control). |
| CB-04 | A course may have at most one **active** certificate builder configuration. Saving for a course that already has one updates that configuration (or prompts to replace — product default: **update in place**). |
| CB-05 | On save, the configuration is stored with `course_id`. Issuance for that course prefers this template over the global default. |

### 6.2 Template management

| ID | Requirement |
|----|-------------|
| CB-06 | Admin can **name a new template** (1–120 chars, trimmed). Names must be unique across `certificate_templates` (existing 409 behavior). |
| CB-07 | Admin can **select an existing template** to use as a starting point; editing then saves as update of that template **or** “Save as new” if renamed to an unused name. |
| CB-08 | Builder UI shows whether the template is course-scoped vs global default (`is_default`). Setting `is_default` remains optional and out of the primary builder path unless already present in the templates admin UI. |

### 6.3 Background image

| ID | Requirement |
|----|-------------|
| CB-09 | Admin can upload a custom background image via file picker **and** drag-and-drop onto a drop zone. |
| CB-10 | Allowed types: JPG and PNG (align with existing thumbnail upload). Max size: 5 MB (same as thumbnails unless product raises it). |
| CB-11 | After upload, the preview shows the image as the certificate background (`background-size: cover`, centered). |
| CB-12 | Admin can remove the custom background; fallback is the platform default (`plain` artwork or solid white — default: **plain** preset). |
| CB-13 | Existing preset artwork keys remain available as an optional secondary choice; custom upload takes precedence when set. |

### 6.4 Layout orientation

| ID | Requirement |
|----|-------------|
| CB-14 | Admin toggles **Landscape** (default) or **Portrait**. |
| CB-15 | Landscape page size: `11in × 8.5in`. Portrait: `8.5in × 11in`. |
| CB-16 | Preview and PDF/`@page` size must match the selected orientation. |

### 6.5 Text content and placeholders

| ID | Requirement |
|----|-------------|
| CB-17 | Admin defines certificate body wording in a text field (plain text for v1; rich text optional stretch). |
| CB-18 | Supported placeholders (must render in preview and on issue): |

| Placeholder | Meaning | Sample preview value |
|-------------|---------|----------------------|
| `{{recipient_name}}` | Student display name | Jane Doe |
| `{{user_name}}` | Alias of recipient (existing token) | Jane Doe |
| `{{course_title}}` | Course title | Security Training |
| `{{completion_date}}` | Completion / issue date (localized) | July 14, 2026 |
| `{{issued_at}}` | Alias of completion/issue date | July 14, 2026 |
| `{{score}}` | Quiz score percent | 92 |
| `{{certificate_id}}` | Non-consuming sample ID in preview | CERT-2026-000001 |

| ID | Requirement |
|----|-------------|
| CB-19 | UI lists insertable placeholders (click-to-insert into the text field). |
| CB-20 | Unknown `{{tokens}}` are left unchanged in the rendered output (no crash). |
| CB-21 | Text is escaped for XSS when interpolated into HTML (same safety model as `certificate_template.render_certification_template`). |

**Default body text** (English) when creating a new config:

```text
This certifies that {{recipient_name}} has successfully completed {{course_title}} on {{completion_date}}.
```

### 6.6 Real-time preview and Review step

| ID | Requirement |
|----|-------------|
| CB-22 | While configuring, a preview pane updates live (debounced ~300ms) when course, orientation, background, or body text changes. |
| CB-23 | Preview uses sample data (or selected course title + sample student) and must not create a certificate row or consume ID sequence. |
| CB-24 | **Review** presents a larger (near print-scale) preview so the admin can verify alignment, text readability, and background image quality. |
| CB-25 | Admin cannot Save until required fields are valid (course, unique template name, orientation). Background is optional. Body text is required (non-empty after trim). |
| CB-26 | On Review, primary actions: **Back** (return to Configure) and **Save** (persist). |
| CB-27 | Successful Save shows confirmation and navigates to the templates list or the course’s certificate section. |

### 6.7 Persistence and issuance behavior

| ID | Requirement |
|----|-------------|
| CB-28 | Save creates or updates a `certificate_templates` document with builder fields (see data model). |
| CB-29 | Course document (or a dedicated link field on the template) records which template is active for that course. |
| CB-30 | On quiz pass / certificate create, resolver order: **course-linked template → explicit `template_id` → global `is_default` → built-in default HTML**. |
| CB-31 | Changing a course template does not rewrite historical certificates unless admin uses existing “apply to course” customize (optional follow-up: offer “Update already-issued certificates”). |

---

## 7. Data Model

### 7.1 Extensions to `certificate_templates`

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Unique (existing) |
| `course_id` | string \| null | Null = global; set for builder configs |
| `orientation` | `"landscape"` \| `"portrait"` | Default `"landscape"` |
| `background` | string | Existing preset key when no custom image |
| `background_image_url` | string \| null | Public URL from upload API |
| `body_text` | string | Admin wording with placeholders |
| `html` | string | Rendered/composed HTML used at issue time (generated from builder fields on save) |
| `primary_color` | string | Keep existing defaults |
| `secondary_color` | string | Keep existing defaults |
| `is_default` | bool | Global default only; course-linked templates should not be default |
| `created_at` / `updated_at` | ISO string | Existing |

### 7.2 Course link

Prefer storing `course_id` on the template **and** optionally `certificate_template_id` on the course for O(1) lookup:

```text
courses.certificate_template_id → certificate_templates._id
certificate_templates.course_id → courses._id
```

On save, keep both sides in sync.

### 7.3 Placeholder compatibility

Renderer must accept both builder aliases and legacy tokens:

- `{{recipient_name}}` ↔ `{{user_name}}`
- `{{completion_date}}` ↔ `{{issued_at}}`

---

## 8. API Surface

### 8.1 New / extended endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/uploads/certificate-background` | Admin upload; JPG/PNG ≤ 5MB; returns `{ url }` (mirror thumbnail upload) |
| `POST` | `/certificate-templates` | Extend create payload with `course_id`, `orientation`, `background_image_url`, `body_text` |
| `PUT` | `/certificate-templates/{id}` | Same fields on update |
| `GET` | `/certificate-templates?course_id=` | Optional filter for course-scoped templates |
| `POST` | `/certificate-templates/preview` **or** extend `POST /certificates/preview` | Accept builder fields + sample data; return HTML (and optional PDF) |

### 8.2 Validation rules

- `course_id` must reference an existing course when provided.
- `orientation` ∈ `{landscape, portrait}`.
- `name` unique; conflict → `409`.
- `body_text` required, max length e.g. 4000 chars.
- Only admin role.

### 8.3 Upload

- Reuse patterns from `POST /uploads/thumbnail` and `upload_utils`.
- Store under `uploads/certificate-backgrounds/`.
- Public URL: `/api/uploads/certificate-backgrounds/{filename}`.

---

## 9. UI Specification

### 9.1 Page / route

- Suggested route: `/admin/certificate-builder` with query `?course_id=` and optional `?template_id=`.
- Also accessible as a step/dialog from Admin Certificates → Templates (“Create with Builder”).

### 9.2 Configure panel (left / top on mobile)

1. **Course** — required select.
2. **Template name** — text input; optional select-existing control above.
3. **Orientation** — two-option toggle: Landscape (default) | Portrait.
4. **Background** — drop zone + file input; thumbnail of current image; Remove; optional preset select.
5. **Certificate text** — textarea with placeholder chips.
6. Primary nav: **Continue to Review** (enabled when valid).

### 9.3 Preview panel (right / below on mobile)

- Scaled certificate frame matching orientation aspect ratio.
- Updates live from form state.
- Note: “Sample data — not a real certificate.”

### 9.4 Review step

- Full-width preview (scrollable on small screens).
- Checklist helper text: alignment, readability, image quality.
- Actions: **Back**, **Save**.
- Saving shows loading state; disable double-submit.

### 9.5 Design constraints

- Follow existing LearnHub admin patterns (`DashboardLayout`, `PageHeader`, Swiss / IKB styling).
- Do not invent a new marketing-style landing page; this is an admin tool.
- Mobile: stacked configure → preview → review; drop zone usable on touch devices.

---

## 10. Rendering Rules

1. Compose final HTML from orientation dimensions + background (image URL or preset artwork) + escaped/interpolated `body_text` + standard chrome (brand frame optional; v1 may use simplified layout centered on the background).
2. Preview and issued PDF must use the same composition path.
3. Localization of dates follows existing `format_certificate_date` / course language when issuing; preview uses course language when `course_id` is set, else UI language / English.

---

## 11. Acceptance Criteria

- [ ] Admin can open builder, select a course, name a unique template, set landscape/portrait, upload a background via drag-and-drop, enter body text with placeholders, see live preview, open Review, and Save successfully.
- [ ] Saved template appears in Admin Certificates → Templates and is linked to the course.
- [ ] Passing a quiz for that course issues a certificate using the saved configuration (correct orientation, background, substituted text).
- [ ] Preview does not insert DB certificate rows or increment ID sequence.
- [ ] Duplicate template names are rejected with a clear error.
- [ ] Invalid image types / oversized files are rejected with clear errors.
- [ ] Non-admins cannot access builder APIs or route.
- [ ] Portrait and landscape both produce correctly sized HTML/PDF.

---

## 12. Test Plan

| Layer | Cases |
|-------|--------|
| Unit | Placeholder alias mapping; orientation page size; background URL vs preset precedence; XSS escaping of body text |
| API | Create/update with `course_id`; uniqueness; upload validation; preview without persistence; issuance resolver order |
| Frontend | Form validation; drag-and-drop upload; debounce preview; Review gating; dirty cancel confirm |
| Integration | End-to-end: save builder config → submit passing quiz → download PDF matches config |

---

## 13. Implementation Notes (for engineering)

1. **Prefer extending** `certificate_templates` + Admin Certificates Templates tab / new builder page over a parallel collection.
2. **Generate `html` on save** from builder fields so existing `render_certification_template` / PDF pipeline keeps working.
3. **Reuse** `ThumbnailUpload` patterns for drag-and-drop UX (add DnD if not present) and `upload_utils` for validation.
4. **Extend** `resolve_certificate_template` to accept `course_id` and prefer course-linked templates.
5. Keep preset backgrounds for backward compatibility with certificates that lack `background_image_url`.

---

## 14. Open Questions

| # | Question | Suggested default |
|---|----------|-------------------|
| 1 | Rich text vs plain text for body? | Plain text + newlines → `<br>` for v1 |
| 2 | One template per course hard limit? | Yes — update in place |
| 3 | Should builder replace the raw-HTML template editor? | No — keep advanced HTML editor; builder is the primary path for course configs |
| 4 | Re-issue / update historical certs on save? | No by default; optional confirm later |
| 5 | Max background resolution? | Cap longest edge at 3000px on upload (optional optimization) |

---

## 15. Summary

The Certificate Builder is an **admin-only, course-scoped configuration flow**: associate a course, name or select a template, set background (upload + DnD), orientation (landscape default / portrait), and wording with placeholders, then **Review** a real-time preview and **Save**. It builds on LearnHub’s existing certificate template, preview, and PDF stack while closing the gaps around course binding, custom imagery, orientation, and guided review.
