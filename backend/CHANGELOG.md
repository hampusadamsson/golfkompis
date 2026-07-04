# Changelog

## [1.1.0](https://github.com/hampusadamsson/golfkompis/compare/golfkompis-backend-v1.0.1...golfkompis-backend-v1.1.0) (2026-07-04)


### Features

* add mingolf credentials to user account, remove age ([fb11b34](https://github.com/hampusadamsson/golfkompis/commit/fb11b34e7cf8ca6ede55743e277902d09abc51a4))
* backend MinGolf endpoints use session cookie + DB creds ([410269d](https://github.com/hampusadamsson/golfkompis/commit/410269dc7c158d2719f25f5f9f81c8094828f9ae))
* html email templates via jinja2 for verification and reset flows ([b23ecc9](https://github.com/hampusadamsson/golfkompis/commit/b23ecc97222ca2eb38bd8f71508702e83fd80da5))
* **queue:** add CRUD routes, async worker, and wire into lifespan ([9a0d2f4](https://github.com/hampusadamsson/golfkompis/commit/9a0d2f415d8171dd616c91ccf90db23bc1fc97d9))
* **queue:** add queue settings, models, schemas, and email senders ([fb89eb1](https://github.com/hampusadamsson/golfkompis/commit/fb89eb1da2f0410c2961988731d706ead5c3afe7))
* verify MinGolf creds before persisting on /users/me/mingolf ([7d7b5d9](https://github.com/hampusadamsson/golfkompis/commit/7d7b5d9fa26e55915a38059cde766e8920ff5e32))


### Bug Fixes

* I3/I4/I17/M10 — sequence guard, verify re-run, global 401 interceptor ([6332da6](https://github.com/hampusadamsson/golfkompis/commit/6332da6fe4478b5044a2369402c436f733a430fc))
* make user.username column nullable to match optional schema ([eb65761](https://github.com/hampusadamsson/golfkompis/commit/eb65761315fc1ce1eb8cff5e6bfe2715128a3fcf))
* make username optional in UserCreate and UserRead schemas ([0780179](https://github.com/hampusadamsson/golfkompis/commit/078017989d400f5684af7aa7f143c9cd239bc038))
* point auth email URL defaults at frontend routes, not backend endpoints ([1b84a1f](https://github.com/hampusadamsson/golfkompis/commit/1b84a1f6323adf1eb27f527b08af2b0130dd324f))
* test backend OK now ([5217323](https://github.com/hampusadamsson/golfkompis/commit/52173233702155850c64219bf5b47c1e4b4d9e8c))


### Documentation

* add root README with build/deploy/mail guide, slim backend+frontend READMEs ([68e8133](https://github.com/hampusadamsson/golfkompis/commit/68e8133605c7d60a25431820e14133a1d44a8b4b))


### Code Refactoring

* **config:** replace two frontend URL settings with single AUTH_FRONTEND_BASE_URL ([842be98](https://github.com/hampusadamsson/golfkompis/commit/842be982604296c85b6c6c7cca367a6f19b938ad))

## [1.0.1](https://github.com/hampusadamsson/golfkompis/compare/golfkompis-v1.0.0...golfkompis-v1.0.1) (2026-04-26)


### Documentation

* added badges ([b6bf184](https://github.com/hampusadamsson/golfkompis/commit/b6bf1846a32ad631fec3555cea871ff0bbd295b0))
* update ([143c422](https://github.com/hampusadamsson/golfkompis/commit/143c422cfef41c5b13aea8e4e86919f7614356e2))

## [1.0.0](https://github.com/hampusadamsson/golfkompis/compare/golfkompis-v0.1.0...golfkompis-v1.0.0) (2026-04-26)


### ⚠ BREAKING CHANGES

* **v2:** full revamp
* **v2:** full revamp

### Features

* add login state guard (_authenticated, _require_login) ([0e75932](https://github.com/hampusadamsson/golfkompis/commit/0e75932c0190236b18795b649a10311ffda9c6c4))
* **api:** add Depends auth, POST /booking, DELETE /bookings/{id}, global error handler ([77ee4fd](https://github.com/hampusadamsson/golfkompis/commit/77ee4fd3d84c5a0439bcf3a8527a20bba3fef973))
* **cli:** shared auth parent parser, --version flag, --course NAME for find ([2c1acc6](https://github.com/hampusadamsson/golfkompis/commit/2c1acc6ec08d768b5dfe241ca16ed4e753f1dd9f))
* configure structlog (logging.py, wire into CLI + FastAPI) ([8abf1d7](https://github.com/hampusadamsson/golfkompis/commit/8abf1d7f868a4b728f99a080e975afde5ef0b6b0))
* **v2:** full revamp ([e5c5195](https://github.com/hampusadamsson/golfkompis/commit/e5c5195bdf01377fb3bc2ab29080e0c51956e494))
* **v2:** full revamp ([e5c5195](https://github.com/hampusadamsson/golfkompis/commit/e5c5195bdf01377fb3bc2ab29080e0c51956e494))


### Code Refactoring

* extract URL constants into endpoints.py ([9fcb41b](https://github.com/hampusadamsson/golfkompis/commit/9fcb41b786f921c80bc06ff62b9182fa41272db6))
* wave 1 foundations ([643fae3](https://github.com/hampusadamsson/golfkompis/commit/643fae3567f313c5f5ed37678635d078266a2e4d))
