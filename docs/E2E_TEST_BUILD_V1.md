# E2E test-build profile (App Factory)

White-label E2E apps use extra dart-defines and CLI flags. The app-build-manifest schema is unchanged (`release.channel` remains `dev` | `pilot` | `production`).

```bash
app-factory build-android path/to/manifest.yaml \
  --customer-app ../BusinessForge-FlutterApp-main \
  --e2e-test --e2e-environment demo \
  --e2e-run-id bf-e2e-app-20260901-001 \
  --debug --format apk --skip-tests
```

`--e2e-test` fails closed if `api_base_url` is production `api.bforge.de`, the environment is not `demo`, or `public_app_id` is missing. Debug APK only (no AAB, no Play Store).

Dart-defines added: `E2E_TEST_BUILD=true`, `BF_E2E_ENVIRONMENT`, optional `BF_E2E_RUN_ID`.
