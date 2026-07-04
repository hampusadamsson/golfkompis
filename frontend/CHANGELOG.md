# Changelog

## [0.1.0](https://github.com/hampusadamsson/golfkompis/compare/golfkompis-frontend-v0.0.1...golfkompis-frontend-v0.1.0) (2026-07-04)


### Features

* add auth route pages (login, register, forgot/reset-password, verify, account) ([5e5100f](https://github.com/hampusadamsson/golfkompis/commit/5e5100f33874cda6c16b7568e1921c8be1827630))
* add currentUser store, boot session check, update Navbar ([7c780e9](https://github.com/hampusadamsson/golfkompis/commit/7c780e94145a3b179aaab83babbc2ee8dbe95d9a))
* add mingolf credentials to user account, remove age ([fb11b34](https://github.com/hampusadamsson/golfkompis/commit/fb11b34e7cf8ca6ede55743e277902d09abc51a4))
* add mingolfProfile runes store + hydrate on session restore ([0ca8001](https://github.com/hampusadamsson/golfkompis/commit/0ca8001fca295d985f5129b378b93c6083476b1c))
* add users API endpoint module + cookieAuth flag ([5c5a852](https://github.com/hampusadamsson/golfkompis/commit/5c5a85239d7691d109b9bd9733dd7a6ff86de5cd))
* map 412 to mingolf_not_linked; add MinGolf profile card to /profile ([f340751](https://github.com/hampusadamsson/golfkompis/commit/f340751d5454dda61bfeba256c4c1c7f1a0be6b3))
* proxy /auth and /users to backend in dev ([bffb41e](https://github.com/hampusadamsson/golfkompis/commit/bffb41ea5d340ef4505bb44670966655d38c946e))
* **queue:** add enqueue button to BookingFind ([07c3745](https://github.com/hampusadamsson/golfkompis/commit/07c3745cc1e9984cb1177c1ea09aa0286138773f))
* **queue:** add queue API client ([081f4bc](https://github.com/hampusadamsson/golfkompis/commit/081f4bcac17e9726b5950b44a5b540d41a8f97b2))
* **queue:** add QueueList and QueueEntryCard components ([e2dadf2](https://github.com/hampusadamsson/golfkompis/commit/e2dadf2392acd1bfca98cb8ac76f881b86a2c3ca))
* **queue:** mount QueueList on /book page ([2149815](https://github.com/hampusadamsson/golfkompis/commit/2149815e164e66cc92f69fbcf07a805e3600ff99))
* remove delete-account section from /profile/account ([c87f45b](https://github.com/hampusadamsson/golfkompis/commit/c87f45b6f6c5fe8ded993a2b40d36a4846a04ef6))


### Bug Fixes

* I3/I4/I17/M10 — sequence guard, verify re-run, global 401 interceptor ([6332da6](https://github.com/hampusadamsson/golfkompis/commit/6332da6fe4478b5044a2369402c436f733a430fc))
* **queue:** fix button layout and mobile width ([d5a8037](https://github.com/hampusadamsson/golfkompis/commit/d5a80378a59d499afd7f6cb11928877212a0458b))
* **queue:** fix double-load on mount in QueueList ([aa38811](https://github.com/hampusadamsson/golfkompis/commit/aa38811be36e3b347b5f64d3cfecbd80648d9215))
* **queue:** fix stop-time label in edit form ([f40bcd8](https://github.com/hampusadamsson/golfkompis/commit/f40bcd8a1910f595e43b88ddd887c63b7b936538))
* **queue:** remove duplicate type definitions, import from types.ts ([86d8caf](https://github.com/hampusadamsson/golfkompis/commit/86d8cafb14ea33e41eea1073dbae380a180c499c))
* sync account form fields from currentUser store via $effect ([71b5e76](https://github.com/hampusadamsson/golfkompis/commit/71b5e769637aa69a513d343ec3c59b183fcab046))


### Documentation

* add root README with build/deploy/mail guide, slim backend+frontend READMEs ([68e8133](https://github.com/hampusadamsson/golfkompis/commit/68e8133605c7d60a25431820e14133a1d44a8b4b))


### Code Refactoring

* API client uses cookie auth only; drop credentials option ([26b30af](https://github.com/hampusadamsson/golfkompis/commit/26b30af6898b71de9e965203300558db625d3a43))
* remove credentials store; all components use cookie auth + currentUser ([a745604](https://github.com/hampusadamsson/golfkompis/commit/a745604215c0d7b4f50fa8680780b129d3294ff5))
