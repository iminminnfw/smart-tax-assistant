# SEC API Documentation

รายละเอียด API สำหรับดึงข้อมูลกองทุนรวมจากสำนักงาน ก.ล.ต.

---

## 1. รายชื่อบริษัทจัดการกองทุนรวม (บลจ.)

ข้อมูลรายชื่อบริษัทจัดการกองทุนรวม (บลจ.) ที่อยู่ภายใต้การกำกับดูแลของสำนักงาน ก.ล.ต.

> **Note:** สามารถนำรหัสบริษัทหลักทรัพย์จัดการกองทุน (`unique_id`) ไปใช้ร่วมกับ Fund API ข้ออื่น เช่น ข้อ 2 เพื่อค้นหากองทุนที่ บลจ. นั้นๆ บริหารดูแล

### Endpoint

```
GET /v1/fund/general-info/amcs
```

### Headers

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `Ocp-Apim-Subscription-Key` | 🔴 **required** | string | คีย์ API เฉพาะของคุณสำหรับการยืนยันตัวตน |

### Query Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `current_page` | 🔴 **required** | integer | ระบุหน้าที่จะดึงข้อมูล (default: `1`) |

### Response

**Content-Type:** `application/json`

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | ข้อความสถานะของการเรียก API |
| `current_page` | number | หน้าปัจจุบัน |
| `total_pages` | number | จำนวนหน้าทั้งหมด |
| `page_size` | number | จำนวนรายการต่อหน้า |
| `total_items` | number | จำนวนรายการทั้งหมด |
| `items` | array\<object\> | รายการข้อมูลหลักที่ส่งกลับมา |

#### Items Object

| Field | Type | Description |
|-------|------|-------------|
| `unique_id` | string | รหัสบริษัทหลักทรัพย์จัดการกองทุน |
| `comp_name_th` | string | ชื่อบริษัทหลักทรัพย์จัดการกองทุน (ภาษาไทย) |
| `comp_name_en` | string | ชื่อบริษัทหลักทรัพย์จัดการกองทุน (ภาษาอังกฤษ) |
| `last_upd_date` | datetime | วันที่แก้ไขข้อมูลล่าสุด |

### Example Code

```python
import requests

url = "https://api.sec.or.th/v1/fund/general-info/amcs"
headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "Ocp-Apim-Subscription-Key": "YOUR_API_KEY"
}
params = {
    "current_page": 1
}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.json())
```

---

## 2. กองทุนรวมภายใต้การบริหารจัดการของ บลจ. และลักษณะทั่วไปของแต่ละกองทุน

ข้อมูลกองทุนรวมภายใต้การบริหารจัดการของแต่ละบริษัทหลักทรัพย์จัดการกองทุน (บลจ.) พร้อมลักษณะทั่วไปของแต่ละกองทุน เช่น:
- สถานะกองทุน
- นโยบายการลงทุน
- ลักษณะโครงการ
- อายุโครงการ
- ชนิดหน่วยลงทุน (Class Fund)
- ข้อมูลกองทุนหลัก (กรณี Feeder Fund)

> **Note:** หากต้องการดึงข้อมูลเฉพาะกองที่ยังมีสถานะ active อยู่ในปัจจุบัน ให้กรองผลลัพธ์ด้วยคอลัมน์ `fund_status` ที่มีค่าเป็น `'IPO'` หรือ `'Registered'`

### Endpoint

```
GET /v1/fund/general-info/profiles
```

### Headers

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `Ocp-Apim-Subscription-Key` | 🔴 **required** | string | คีย์ API เฉพาะของคุณสำหรับการยืนยันตัวตน |

### Query Parameters

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| `current_page` | 🔴 **required** | integer | ระบุหน้าที่จะดึงข้อมูล (default: `1`) |
| `search` | optional | string | ค้นหาด้วย ชื่อ บลจ. (TH/EN) หรือรหัสนิติบุคคล |

### Example Code

```python
import requests

url = "https://api.sec.or.th/v1/fund/general-info/profiles"
headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "Ocp-Apim-Subscription-Key": "YOUR_API_KEY"
}
params = {
    "current_page": 1,
    "search": "กสิกร"  # optional
}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.json())
```

---

## Base URL

```
https://api.sec.or.th
```

## Authentication

ทุก API ต้องส่ง Header `Ocp-Apim-Subscription-Key` พร้อม API Key ที่ได้รับจากการลงทะเบียน
