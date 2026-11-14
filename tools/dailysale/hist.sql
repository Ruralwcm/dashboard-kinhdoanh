-- Dailysale · lịch sử 6 tháng + 6 tuần theo CH (dataset asia-southeast1)
-- Mỗi CH 1 dòng, mảng 12 kỳ: 6 tháng (M-5..M, tháng hiện tại = MTD) rồi 6 tuần (W-5..W, tuần hiện tại = WTD).
-- rv/dn: doanh thu & số ngày có bán · rvl/dnl: cùng kỳ năm trước (tháng: cùng ngày lịch; tuần: lùi 364 ngày)
-- sl: shrink - loss + coupon (chi phí S&L&C; loss âm = mất) · sll: cùng kỳ năm trước
WITH
P AS (SELECT MAX(date) AS D FROM `rural-data-analystic.daily_sale_new_report.daily_sales` WHERE revenue > 0),
B AS (
  SELECT i AS k, DATE_SUB(DATE_TRUNC(D, MONTH), INTERVAL 5 - i MONTH) AS b0,
         LEAST(LAST_DAY(DATE_SUB(DATE_TRUNC(D, MONTH), INTERVAL 5 - i MONTH)), D) AS b1, 'M' AS t
  FROM P, UNNEST(GENERATE_ARRAY(0, 5)) i
  UNION ALL
  SELECT 6 + i, DATE_SUB(DATE_TRUNC(D, WEEK(MONDAY)), INTERVAL (5 - i) * 7 DAY),
         LEAST(DATE_ADD(DATE_SUB(DATE_TRUNC(D, WEEK(MONDAY)), INTERVAL (5 - i) * 7 DAY), INTERVAL 6 DAY), D), 'W'
  FROM P, UNNEST(GENERATE_ARRAY(0, 5)) i),
BL AS (SELECT k, t, b0, b1,
         IF(t = 'M', DATE_SUB(b0, INTERVAL 1 YEAR), DATE_SUB(b0, INTERVAL 364 DAY)) AS l0,
         IF(t = 'M', DATE_SUB(b1, INTERVAL 1 YEAR), DATE_SUB(b1, INTERVAL 364 DAY)) AS l1 FROM B),
RNG AS (SELECT MIN(l0) lo0, MAX(b1) hi FROM BL),
S AS (SELECT store, date, revenue rv FROM `rural-data-analystic.daily_sale_new_report.daily_sales`, RNG WHERE date BETWEEN lo0 AND hi),
C AS (
  SELECT store, date, SUM(v) v FROM (
    SELECT store, date, shrinkage_value v FROM `rural-data-analystic.daily_sale_new_report.shrinkage`
    UNION ALL SELECT store, date, -loss_value FROM `rural-data-analystic.daily_sale_new_report.loss`
    UNION ALL SELECT store, date, coupon_discount_value FROM `rural-data-analystic.daily_sale_new_report.coupon`
  ), RNG WHERE date BETWEEN lo0 AND hi GROUP BY 1, 2),
X AS (
  SELECT s.store, BL.k,
    SUM(IF(s.date BETWEEN BL.b0 AND BL.b1, s.rv, 0)) rv,
    COUNTIF(s.date BETWEEN BL.b0 AND BL.b1 AND s.rv > 0) dn,
    SUM(IF(s.date BETWEEN BL.l0 AND BL.l1, s.rv, 0)) rvl,
    COUNTIF(s.date BETWEEN BL.l0 AND BL.l1 AND s.rv > 0) dnl
  FROM S s CROSS JOIN BL GROUP BY 1, 2),
Y AS (SELECT c.store, BL.k, SUM(IF(c.date BETWEEN BL.b0 AND BL.b1, c.v, 0)) sl, SUM(IF(c.date BETWEEN BL.l0 AND BL.l1, c.v, 0)) sll
      FROM C c CROSS JOIN BL GROUP BY 1, 2),
Z AS (SELECT X.store, X.k, X.rv, X.dn, X.rvl, X.dnl, IFNULL(Y.sl, 0) sl, IFNULL(Y.sll, 0) sll FROM X LEFT JOIN Y USING (store, k))
SELECT store,
  ARRAY_AGG(ROUND(rv, 2) ORDER BY k) rv, ARRAY_AGG(dn ORDER BY k) dn,
  ARRAY_AGG(ROUND(rvl, 2) ORDER BY k) rvl, ARRAY_AGG(dnl ORDER BY k) dnl,
  ARRAY_AGG(ROUND(sl, 2) ORDER BY k) sl, ARRAY_AGG(ROUND(sll, 2) ORDER BY k) sll
FROM Z GROUP BY store
