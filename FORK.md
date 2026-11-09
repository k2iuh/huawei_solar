# Fork of wlcrs/huawei_solar

This fork carries a small number of patches on top of an upstream release. Branch `k2iuh` is always
"upstream release tag + the commits below". The upstream release it is based on is in `.fork-base`.
Versions are `<upstream version>+k2iuh.<n>`, for example `2.1.5+k2iuh.1`.

Each patch is exactly one commit with its code and tests, so that a patch commit can serve as the
base of an upstream pull request. The last commit holds the fork-only files (this file, the
workflows, `.fork-base`, the manifest version). To change a patch, amend its commit
(`git commit --fixup=<commit>` and `git rebase -i --autosquash <base tag>`) and force-push the
branch. Do not add fix commits on top. Then raise `<n>` and tag the new head.

Install it in HACS as a custom repository (`https://github.com/k2iuh/huawei_solar`, type
Integration) instead of the upstream entry. The domain stays `huawei_solar`, so existing config
entries and entities are kept.

## Patches

### Library from the k2iuh/huawei-solar-lib fork

`manifest.json` installs the library from a tag of
[k2iuh/huawei-solar-lib](https://github.com/k2iuh/huawei-solar-lib). That fork accepts optimizer
file 0x44 when the inverter returns a CRC that does not match a valid payload
([wlcrs/huawei-solar-lib#39](https://github.com/wlcrs/huawei-solar-lib/issues/39), declined
upstream). The fork's `FORK.md` describes the patch.

The requirement uses the form `git+<url>@<tag>#huawei-solar==<version>`. Home Assistant can
check the installed version against `==<version>`. With the form `huawei-solar @ git+<url>` it
cannot, and it reinstalls the library on every start, which delays startup by about 15 seconds.

### Load optimizer data in the background

Upstream reads two optimizer files during the config entry setup: the device information (0x45)
and the current values (0x44). On some inverters each file frame takes over a second, so this
delays the setup, and with it Home Assistant's startup, by 40 seconds or more.

This fork caches the optimizer device information in `.storage/huawei_solar.optimizers.<serial>`
and builds the optimizer devices and entities from the cache. Only the very first setup reads
file 0x45 synchronously. After setup, a background task fetches the current values and reads
0x45 again. If the optimizers changed, it updates the cache and reloads the config entry.

- Code: `optimizers.py`, plus the optimizer block in `_setup_inverter_device_data` and the
  background task at the end of `async_setup_entry` in `__init__.py`. `async_setup_entry` in
  `sensor.py` adds the optimizer entities without `update_before_add`, which would otherwise
  wait for file 0x44.
- Candidate for an upstream pull request. Upstream's AI policy requires that a human submits and
  explains it. Drop this patch when upstream has an equivalent.

### Tests

Upstream has no tests. `tests/` covers the patches above:

```bash
uv run -p 3.14 --no-project --with-requirements requirements_test.txt pytest -c tests/pytest.ini tests
```

## Updating to a new upstream release

The `Fork sync` workflow runs every Monday. When upstream has a newer release than `.fork-base`, it
rebases the fork commits onto it in a `sync/<tag>` branch, sets the version to
`<tag>+k2iuh.1`, runs the tests and opens an issue with the result. A conflict in `manifest.json`
(every upstream release bumps its version) is resolved automatically; any other conflict is
reported. It never publishes anything. To finish an update:

1. If the library fork got a new release, point the requirement in `manifest.json` at its tag
   and set the version after `#huawei-solar==` to match.
2. Review the `sync/<tag>` branch and fast-forward `k2iuh` to it.
3. Tag `<tag>+k2iuh.1` and push the tag. The fork has no GitHub releases, so HACS tracks branch
   `k2iuh` and offers the update as soon as the branch moves.
