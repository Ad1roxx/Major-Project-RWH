# MGNREGA geotags — provenance

- **Portal:** https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/
- **Endpoint:** `POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php` (application/x-www-form-urlencoded, no login)
- **Pulled:** 2026-10-04, by `tools/pull_mgnrega.py`
- **Codes:** stage, category and block codes were read from the portal's dropdowns and the browser Network payload on 2026-10-04 (`dropdown_codes.tsv`; categories also in `category_codes.csv`).
- **Stages pulled:** 0 = Phase I: Assets (works started before 1 Nov 2017, tagged retrospectively); 3 = Phase II: After (geotag at completion). Stages 1 and 2 were not pulled.
- Files are saved byte-for-byte as returned. Never edit them.
- `observername` in these files is personal data: raw files only.

## Requests

| # | label | file | timestamp | HTTP | bytes | rows |
|---|---|---|---|---|---|---|
| 1 | stage 0 / 1829001 CHANDRAPUR | `data/raw/mgnrega/stage0/1829001.json` | 2026-10-04T02:44:13+05:30 | 200 | 920022 | 1374 |
| 2 | stage 0 / 1829002 BHADRAVATI | `data/raw/mgnrega/stage0/1829002.json` | 2026-10-04T02:44:20+05:30 | 200 | 1301179 | 1960 |
| 3 | stage 0 / 1829003 WARORA | `data/raw/mgnrega/stage0/1829003.json` | 2026-10-04T02:44:29+05:30 | 200 | 1749995 | 2645 |
| 4 | stage 0 / 1829004 CHIMUR | `data/raw/mgnrega/stage0/1829004.json` | 2026-10-04T02:44:38+05:30 | 200 | 2725006 | 3968 |
| 5 | stage 0 / 1829005 NAGBHIR | `data/raw/mgnrega/stage0/1829005.json` | 2026-10-04T02:44:49+05:30 | 200 | 2951552 | 4439 |
| 6 | stage 0 / 1829006 BRAHMAPURI | `data/raw/mgnrega/stage0/1829006.json` | 2026-10-04T02:44:58+05:30 | 200 | 3350305 | 5055 |
| 7 | stage 0 / 1829008 MUL | `data/raw/mgnrega/stage0/1829008.json` | 2026-10-04T02:45:17+05:30 | 200 | 2345371 | 3466 |
| 8 | stage 0 / 1829009 GONDPIPRI | `data/raw/mgnrega/stage0/1829009.json` | 2026-10-04T02:45:26+05:30 | 200 | 2125217 | 3173 |
| 9 | stage 0 / 1829010 RAJURA | `data/raw/mgnrega/stage0/1829010.json` | 2026-10-04T02:45:36+05:30 | 200 | 963912 | 1424 |
| 10 | stage 0 / 1829011 SAOLI | `data/raw/mgnrega/stage0/1829011.json` | 2026-10-04T02:45:45+05:30 | 200 | 1725517 | 2521 |
| 11 | stage 0 / 1829012 BALLARPUR | `data/raw/mgnrega/stage0/1829012.json` | 2026-10-04T02:45:53+05:30 | 200 | 775324 | 1179 |
| 12 | stage 0 / 1829013 KORPANA | `data/raw/mgnrega/stage0/1829013.json` | 2026-10-04T02:46:01+05:30 | 200 | 712147 | 1006 |
| 13 | stage 0 / 1829014 SINDEWAHI | `data/raw/mgnrega/stage0/1829014.json` | 2026-10-04T02:46:09+05:30 | 200 | 2200106 | 3271 |
| 14 | stage 0 / 1829015 JIVTI | `data/raw/mgnrega/stage0/1829015.json` | 2026-10-04T02:46:18+05:30 | 200 | 776976 | 1160 |
| 15 | stage 0 / 1829016 POMBHURNA | `data/raw/mgnrega/stage0/1829016.json` | 2026-10-04T02:46:30+05:30 | 200 | 1485095 | 2174 |
| 16 | stage 3 / 1829001 CHANDRAPUR | `data/raw/mgnrega/stage3/1829001.json` | 2026-10-04T02:46:40+05:30 | 200 | 1286533 | 1758 |
| 17 | stage 3 / 1829002 BHADRAVATI | `data/raw/mgnrega/stage3/1829002.json` | 2026-10-04T02:46:51+05:30 | 200 | 3563634 | 4881 |
| 18 | stage 3 / 1829003 WARORA | `data/raw/mgnrega/stage3/1829003.json` | 2026-10-04T02:46:59+05:30 | 200 | 1705543 | 2329 |
| 19 | stage 3 / 1829004 CHIMUR | `data/raw/mgnrega/stage3/1829004.json` | 2026-10-04T02:47:07+05:30 | 200 | 3209462 | 4370 |
| 20 | stage 3 / 1829005 NAGBHIR | `data/raw/mgnrega/stage3/1829005.json` | 2026-10-04T02:47:17+05:30 | 200 | 3169645 | 4317 |
| 21 | stage 3 / 1829006 BRAHMAPURI | `data/raw/mgnrega/stage3/1829006.json` | 2026-10-04T02:47:31+05:30 | 200 | 3356576 | 4589 |
| 22 | stage 3 / 1829008 MUL | `data/raw/mgnrega/stage3/1829008.json` | 2026-10-04T02:47:40+05:30 | 200 | 1445736 | 1972 |
| 23 | stage 3 / 1829009 GONDPIPRI | `data/raw/mgnrega/stage3/1829009.json` | 2026-10-04T02:47:47+05:30 | 200 | 3160596 | 4315 |
| 24 | stage 3 / 1829010 RAJURA | `data/raw/mgnrega/stage3/1829010.json` | 2026-10-04T02:47:56+05:30 | 200 | 921096 | 1258 |
| 25 | stage 3 / 1829011 SAOLI | `data/raw/mgnrega/stage3/1829011.json` | 2026-10-04T02:48:04+05:30 | 200 | 3050448 | 4158 |
| 26 | stage 3 / 1829012 BALLARPUR | `data/raw/mgnrega/stage3/1829012.json` | 2026-10-04T02:48:13+05:30 | 200 | 1238180 | 1698 |
| 27 | stage 3 / 1829013 KORPANA | `data/raw/mgnrega/stage3/1829013.json` | 2026-10-04T02:48:20+05:30 | 200 | 629012 | 854 |
| 28 | stage 3 / 1829014 SINDEWAHI | `data/raw/mgnrega/stage3/1829014.json` | 2026-10-04T02:48:27+05:30 | 200 | 1513942 | 2064 |
| 29 | stage 3 / 1829015 JIVTI | `data/raw/mgnrega/stage3/1829015.json` | 2026-10-04T02:48:35+05:30 | 200 | 645785 | 881 |
| 30 | stage 3 / 1829016 POMBHURNA | `data/raw/mgnrega/stage3/1829016.json` | 2026-10-04T02:48:43+05:30 | 200 | 2957311 | 4030 |
| 31 | stage 0 / block All (CHECK ONLY) | `data/raw/mgnrega/check_blockAll_stage0.json` | 2026-10-04T02:48:52+05:30 | 200 | 4 | 0 |
| 32 | stage 3 / block All (CHECK ONLY) | `data/raw/mgnrega/check_blockAll_stage3.json` | 2026-10-04T02:48:59+05:30 | 200 | 4 | 0 |

## Form data and equivalent curl, per request

### 1. stage 0 / 1829001 CHANDRAPUR

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829001
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829001&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 2. stage 0 / 1829002 BHADRAVATI

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829002
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829002&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 3. stage 0 / 1829003 WARORA

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829003
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829003&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 4. stage 0 / 1829004 CHIMUR

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829004
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829004&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 5. stage 0 / 1829005 NAGBHIR

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829005
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829005&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 6. stage 0 / 1829006 BRAHMAPURI

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829006
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829006&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 7. stage 0 / 1829008 MUL

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829008
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829008&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 8. stage 0 / 1829009 GONDPIPRI

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829009
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829009&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 9. stage 0 / 1829010 RAJURA

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829010
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829010&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 10. stage 0 / 1829011 SAOLI

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829011
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829011&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 11. stage 0 / 1829012 BALLARPUR

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829012
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829012&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 12. stage 0 / 1829013 KORPANA

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829013
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829013&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 13. stage 0 / 1829014 SINDEWAHI

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829014
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829014&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 14. stage 0 / 1829015 JIVTI

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829015
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829015&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 15. stage 0 / 1829016 POMBHURNA

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=1829016
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=1829016&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 16. stage 3 / 1829001 CHANDRAPUR

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829001
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829001&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 17. stage 3 / 1829002 BHADRAVATI

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829002
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829002&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 18. stage 3 / 1829003 WARORA

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829003
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829003&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 19. stage 3 / 1829004 CHIMUR

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829004
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829004&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 20. stage 3 / 1829005 NAGBHIR

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829005
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829005&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 21. stage 3 / 1829006 BRAHMAPURI

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829006
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829006&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 22. stage 3 / 1829008 MUL

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829008
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829008&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 23. stage 3 / 1829009 GONDPIPRI

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829009
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829009&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 24. stage 3 / 1829010 RAJURA

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829010
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829010&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 25. stage 3 / 1829011 SAOLI

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829011
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829011&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 26. stage 3 / 1829012 BALLARPUR

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829012
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829012&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 27. stage 3 / 1829013 KORPANA

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829013
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829013&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 28. stage 3 / 1829014 SINDEWAHI

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829014
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829014&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 29. stage 3 / 1829015 JIVTI

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829015
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829015&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 30. stage 3 / 1829016 POMBHURNA

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=1829016
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=1829016&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 31. stage 0 / block All (CHECK ONLY)

```
username=unauthourized
stage=0
state_code=18
district_code=1829
block_code=All
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=0&state_code=18&district_code=1829&block_code=All&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```

### 32. stage 3 / block All (CHECK ONLY)

```
username=unauthourized
stage=3
state_code=18
district_code=1829
block_code=All
panchayat_code=All
financial_year=All
accuracy=0
category_id=All
sub_category_id=All
start_date=1998-09-30
end_date=2026-10-04
```

```sh
curl -sS -X POST https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/reports/accepted_geotags.php -H 'Content-Type: application/x-www-form-urlencoded' --data 'username=unauthourized&stage=3&state_code=18&district_code=1829&block_code=All&panchayat_code=All&financial_year=All&accuracy=0&category_id=All&sub_category_id=All&start_date=1998-09-30&end_date=2026-10-04'
```
