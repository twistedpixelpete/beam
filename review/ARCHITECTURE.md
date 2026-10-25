# Beam Review architecture

## Implemented vertical slice

Beam Authoring → `review_export.py` → immutable local Review Package → static Three.js viewer.

The authoring exporter calls the existing `study_reporting.document` and validation contract. It does not introduce a second projector or optics model. The only additional data are presentation endpoints, exact camera projection matrices and geometry-node associations. Projectors are reconstructed as browser objects; their exported first-hit helper endpoints preserve the display-only frustum termination rule. Analysis comes directly from Authoring.

Evaluated meshes are copied into a temporary Blender scene, preserving UV layers and material references. World transforms are converted from scene units to metres; glTF handles the Z-up to Y-up rotation. The original scene/context and temporary data are restored on success or failure. Study data stay in Blender's documented Z-up metre convention; the browser converts points `[x,y,z]` to `[x,z,-y]` and prepends an X-axis -90° rotation to orientations. Camera projection matrices use metre clipping and orthographic scale. Study View aspect is retained by letterboxing.

`server.mjs` is a local read-only static server. No API, database or Blender runtime runs in the viewer. It rejects writes, restricts served roots and binds to 127.0.0.1. The browser verifies JSON/GLB hashes before rendering and rejects GLB resources referencing external URLs. File hashes detect package mismatch; they are not a trust signature.

## Future hosted workflow — design only

Publish a new immutable revision under an existing project. Upload the complete package to private object storage through an authenticated authoring endpoint; verify size, schema, hashes and resource paths before accepting it. Retain the prior revisions. A client link identifies one specific revision, not a mutable latest alias.

Use separate cryptographically random identifiers for the project, revision and share link. Store revision ownership and file inventory server-side. Store share policy separately so a link can be revoked or expire without deleting revision history. Do not treat knowledge of a storage URL as authorisation.

Serve via HTTPS. Optional passwords are verified server-side using a salted modern password hash (for example Argon2id) with rate limiting. Successful checks create a short-lived secure, HttpOnly, SameSite session scoped to that share/revision. No plaintext password or verifier goes into JavaScript, the package or a URL. Every manifest, JSON, GLB, texture and thumbnail request must pass the same access check; protecting only the HTML page is insufficient. Avoid public CDN caching of private assets. Revocation/expiry must be checked on subsequent requests, with short-lived asset authorisation if signed URLs are used.

Keep published packages read-only. Authoring stays in Blender. Publishing should create a new revision by default, with an explicit label such as R01/R02. User accounts, comments, approvals, revision comparison, billing and PATCH integration remain later work. No hosted service or password protection is implemented by this prototype.

## Dependencies

Three.js 0.180.0, MIT licence, pinned in package-lock.json. GLB loading uses the official [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html); navigation uses [OrbitControls](https://threejs.org/docs/pages/OrbitControls.html). No remote script imports are used at runtime.
