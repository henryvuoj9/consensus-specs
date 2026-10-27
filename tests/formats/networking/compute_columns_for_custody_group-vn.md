# `compute_columns_for_custody_group` tests

Các test `compute_columns_for_custody_group` cung cấp các sanity check (kiểm tra
cơ bản) cho tính đúng đắn của hàm helper `compute_columns_for_custody_group`.

## Test case format

### `meta.yaml`

```yaml
description: string            -- optional: description of test case, purely for debugging purposes.
custody_group: int             -- argument: the custody group index.
result: list of int            -- output: the list of resulting column indices.
```
