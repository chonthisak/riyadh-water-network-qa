# วิธีเริ่มใช้งาน

## เปิดใน QGIS
1. แตกไฟล์ ZIP ลงโฟลเดอร์ที่เก็บงาน
2. เปิด QGIS แล้วลาก `data/network.gpkg` ลงหน้าต่างแผนที่
3. เลือก `pipes_raw`, `sources`, `valves`, `qa_before`
4. เปิด Layer Properties > Symbology ของ `qa_before` เลือก Categorized และฟิลด์ `code` แล้วกด Classify
5. ใช้ Identify Features หรือเปิด Attribute Table เพื่อดูคำอธิบายและ row_id ของปัญหา
6. เปรียบเทียบกับ `pipes_clean` และ `qa_after` ปิดชั้นข้อมูลก่อนแก้เมื่อดูผลหลังแก้
7. ตั้ง Project CRS เป็น EPSG:32638 บันทึกเป็น `qgis/riyadh-water-network.qgz` และตั้ง Project Properties > General > Save paths เป็น Relative

ยังไม่มีไฟล์ .qgz ที่ทดสอบในโปรแกรมแล้ว จึงใช้ GeoPackage พร้อมคู่มือนี้เป็นจุดเริ่มต้น แผนที่ตัวอย่างอยู่ใน `figures/overview.svg`

## รันการตรวจด้วย Python
เปิด Terminal ในโฟลเดอร์โปรเจกต์ ใช้ Python 3.9 ขึ้นไป:
```
python3 scripts/build.py
python3 -m unittest discover -s tests -v
```
คำสั่งแรกสร้าง GeoJSON รายงาน JSON และแผนที่ใหม่ ไม่เขียน GeoPackage เว้นแต่ระบุ `--ogr2ogr` ตาม README

## ใช้ PostGIS
1. เปิด Postgres.app และเริ่มเซิร์ฟเวอร์
2. สร้างฐานข้อมูลใหม่ชื่อ `riyadh_portfolio` โดยไม่ใช้ฐานข้อมูลของงานอื่น
3. ใช้คำสั่งใน README ตามลำดับ หรือใช้ Query Tool ใน pgAdmin โดยนำบรรทัดที่ขึ้นต้นด้วยเครื่องหมาย backslash ออก และแทน `:pipe_table` ด้วย `water_raw.pipes` หรือ `water_clean.pipes`
4. ใน QGIS เลือก Data Source Manager > PostgreSQL > New แล้วใส่ host, port, database และชื่อผู้ใช้ของคุณ
5. เพิ่มตารางจาก water_raw / water_clean และ view `water_qa.findings` เลือก issue_id เป็น unique key ของ view

ไม่ใส่รหัสผ่านลง GitHub เก็บในระบบจัดการรหัสผ่านหรือ .pgpass ของเครื่องคุณ

## ลง GitHub ด้วย GitHub Desktop
1. File > Add Local Repository แล้วเลือกโฟลเดอร์นี้
2. หากยังไม่ใช่ repository ให้เลือก Create a Repository ที่โฟลเดอร์นี้
3. ตรวจรายการไฟล์ แล้ว commit
4. Publish repository ชื่อ `riyadh-water-network-qa` หากต้องการพอร์ตสาธารณะให้ปิด Keep this code private
5. เพิ่มคำอธิบาย: Synthetic water-network GIS QA with QGIS, PostGIS and reproducible Python checks.

ตัวเลขในพอร์ตเป็นข้อมูลจำลอง ไม่ใช่งานที่เคยทำให้บริษัท และไม่ใช่ผลตรวจระบบประปาจริง
