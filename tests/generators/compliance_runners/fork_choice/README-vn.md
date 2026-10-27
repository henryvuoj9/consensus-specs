# Fork choice compliance test generator

Bộ sinh test (test generator) cho Fork Choice, dùng để tạo ra các test nhằm kiểm
tra mức độ tuân thủ spec của các hiện thực Fork Choice khác nhau.

Đây là hiện thực của phương pháp được mô tả trong
[Fork Choice compliance testing framework](https://hackmd.io/@ericsson49/fork-choice-implementation-vs-spec-testing).

Nghiên cứu sơ bộ cũng đã được thực hiện trong
[repo](https://github.com/txrx-research/fork_choice_test_generation/tree/main)
này.

Để việc áp dụng các test được dễ dàng hơn, chúng tôi tuân theo test format được
mô tả trong
[tài liệu fork choice test formats](../../../formats/fork_choice/README.md), với
một ngoại lệ nhỏ (có thêm một check mới).

Công việc này được hỗ trợ bởi một khoản tài trợ (grant) từ Ethereum Foundation.

# Generating tests

Từ thư mục gốc (root directory):

```
make comptests fc_gen_config=<config>
```

trong đó `config` có thể là: [`tiny`](tiny/), [`small`](small/) hoặc
[`standard`](standard/).

Target này dùng cơ chế collection của pytest và có thể lọc bằng `k=<pattern>`,
theo cùng kiểu với `make test`.

`make comptests` là cách sinh test được hỗ trợ chính thức.

# Running tests

Từ thư mục gốc:

```
make build  # Initialize virtual environment
uv run pytest tests/generators/compliance_runners/fork_choice/runner/test_run.py --test-dir ${test_dir}
```

Có thể thêm các cờ lọc và phân tán (distribution) tùy chọn của pytest như
`-k ...` và `-n logical` khi cần.

# Generating configurations

Các file trong [`tiny`](tiny/), [`small`](small/) và [`standard`](standard/)
được sinh ra bằng [`generate_test_instances.py`](generate_test_instances.py), ví
dụ:

```
make build  # Initialize virtual environment
uv run python -m tests.generators.compliance_runners.fork_choice.generate_test_instances
```

Tuy nhiên, thông thường bạn không cần tự sinh lại chúng.
