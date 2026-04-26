# Device firmware as git submodules

## Goals

- **One firmware = one repository** with its own tags, issues, and clone URL.
- The automation monorepo ([ServerBootShutdownManagemement](https://github.com/tinel-c/ServerBootShutdownManagemement)) **pins** known-good firmware revisions under `device/<name>` without copying source trees by hand.
- **Secrets stay out of git:** each device repo uses templates (`passwords.h.example`, `password.h_template`, `config/.env.example`); the parent repo’s `.gitignore` also ignores common secret paths under `device/**/`.

## Layout

| Path under `device/` | Rule |
|----------------------|------|
| **Directory name** | Prefer the **GitHub repository name** (e.g. `esp32-sms-gateway`, `PlatformIO_ESP8266_Main_Entry`) so paths match upstream and are easy to find. |
| **Submodule** | Always added with `git submodule add <url> device/<path>`. Do not copy firmware trees into the monorepo without a submodule. |

## Adding a new device repository

1. **Create the firmware repository** (empty or with initial import). Ensure it includes:
   - `README.md` (build, flash, config templates).
   - `.gitignore` for build dirs (e.g. PlatformIO `.pio/`), and for local secrets.
   - No committed credentials.
2. **Add the submodule** from the monorepo root:
   ```bash
   git submodule add https://github.com/<org>/<repo>.git device/<repo-name>
   git commit -m "feat(device): add <repo-name> submodule"
   ```
3. **Register it** in [device/README.md](../../device/README.md) (table + upstream link).
4. **Point documentation** to `device/<repo-name>` in any relevant `docs/*.md` (e.g. OTA, architecture).
5. **Parent `.gitignore`** already covers `device/**/include/passwords.h`, `device/**/src/password.h`, and `device/**/.env`. Add a line only if the new project uses a different secret filename.

## Cloning and updating

| Task | Command |
|------|---------|
| Clone monorepo + all submodules | `git clone --recurse-submodules <automation-url>` |
| Submodules after a normal clone | `git submodule update --init --recursive` |
| Update one device to **latest default branch** of its remote | `cd device/<name> && git pull origin <branch>` then from monorepo root: `git add device/<name>` and commit (pins new revision). |
| List submodule status | `git submodule status` |

## Releasing and CI

- Tag **device releases** in the **device repository** (e.g. `v1.0.0` on `esp32-sms-gateway`).
- Tag the **automation** repository when a bundle of submodules and flows is known good; release notes can list each **pinned** submodule commit or tag for reproducible builds.

## Checklist (copy for issues/PRs)

- [ ] Device repo is public (or team has access) and default branch is buildable.
- [ ] `git submodule add` used; `device/README.md` updated.
- [ ] Docs that referenced old paths (if any) updated.
- [ ] No secrets in the submodule’s tracked files.
- [ ] `git submodule update --init --recursive` verified on a fresh clone.

**Existing examples:** [esp32-sms-gateway](https://github.com/tinel-c/esp32-sms-gateway), [PlatformIO_ESP8266_Main_Entry](https://github.com/tinel-c/PlatformIO_ESP8266_Main_Entry).
