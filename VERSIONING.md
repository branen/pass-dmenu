pass-dmenu releases follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).

The following aspects of pass-dmenu are guaranteed to remain
backwards-compatible throughout the major version 1 series:

- The pass-dmenu CLI

- pass-dmenu's interpretation of the following environment variables:
    - `PASSWORD_STORE_DIR`
    - `PASSWORD_STORE_UMASK`
    - `PASSWORD_STORE_DMENU`
    - `PASSWORD_STORE_X_SELECTION`
    - `PASSWORD_STORE_CLIP_TIME`

- pass-dmenu's interpretation of `.pass-dmenu.cache`.
