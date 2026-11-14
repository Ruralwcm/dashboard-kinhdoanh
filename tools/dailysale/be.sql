-- Điểm hòa vốn (SPD tr.đ/ngày) theo CH
SELECT store, ROUND(be_sale, 2) AS be FROM `rural-data-analystic.daily_sale_new_report.catchment` WHERE be_sale > 0
