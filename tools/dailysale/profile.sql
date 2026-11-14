-- Thuộc tính CH (dataset US) — snapshot Storeslist
SELECT ma_sap sap, ten_cua_hang nm, tinh_trang tt, CAST(khai_truong AS STRING) kt, mien mi, phan_vung vu,
       tinh_tp_cu_truoc_1_7 ti, quan_huyen_cu_truoc_1_7 qu, gdv gd, qlkv ql
FROM `rural-data-analystic.admin_hr.store_profile_20261103`
WHERE ma_sap IS NOT NULL AND ma_sap != ''
