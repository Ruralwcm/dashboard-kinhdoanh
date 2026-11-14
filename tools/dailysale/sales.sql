-- Dailysale v9 · số liệu theo CH (dataset asia-southeast1)
-- D = ngày gần nhất có doanh thu (D-1). LY ngày & tuần: lùi 364 ngày (cùng thứ). LY tháng & năm: cùng ngày lịch năm trước.
WITH
P AS (SELECT MAX(date) AS D FROM `rural-data-analystic.daily_sale_new_report.daily_sales` WHERE revenue > 0),
R AS (SELECT D, DATE_SUB(D, INTERVAL 364 DAY) AS DL, DATE_TRUNC(D, WEEK(MONDAY)) AS W0,
        DATE_SUB(DATE_TRUNC(D, WEEK(MONDAY)), INTERVAL 364 DAY) AS WL0,
        DATE_TRUNC(D, MONTH) AS M0, DATE_SUB(DATE_TRUNC(D, MONTH), INTERVAL 1 YEAR) AS ML0, DATE_SUB(D, INTERVAL 1 YEAR) AS ML1,
        DATE_TRUNC(D, YEAR) AS Y0, DATE_SUB(DATE_TRUNC(D, YEAR), INTERVAL 1 YEAR) AS YL0 FROM P),
S AS (SELECT store, date, revenue rv, IFNULL(pos_revenue, revenue) rr, billing_count bl
      FROM `rural-data-analystic.daily_sale_new_report.daily_sales`, R WHERE date BETWEEN R.YL0 AND R.D),
A AS (SELECT s.store,
    SUM(IF(date=D,rv,0)) d_s, SUM(IF(date=D,rr,0)) d_r, SUM(IF(date=D,bl,0)) d_b,
    SUM(IF(date=DL,rv,0)) dl_s, SUM(IF(date=DL,rr,0)) dl_r, SUM(IF(date=DL,bl,0)) dl_b,
    SUM(IF(date BETWEEN W0 AND D,rv,0)) w_s, SUM(IF(date BETWEEN W0 AND D,rr,0)) w_r, SUM(IF(date BETWEEN W0 AND D,bl,0)) w_b, COUNTIF(date BETWEEN W0 AND D AND rv>0) w_n,
    SUM(IF(date BETWEEN WL0 AND DL,rv,0)) wl_s, SUM(IF(date BETWEEN WL0 AND DL,rr,0)) wl_r, SUM(IF(date BETWEEN WL0 AND DL,bl,0)) wl_b, COUNTIF(date BETWEEN WL0 AND DL AND rv>0) wl_n,
    SUM(IF(date BETWEEN M0 AND D,rv,0)) m_s, SUM(IF(date BETWEEN M0 AND D,rr,0)) m_r, SUM(IF(date BETWEEN M0 AND D,bl,0)) m_b, COUNTIF(date BETWEEN M0 AND D AND rv>0) m_n,
    SUM(IF(date BETWEEN ML0 AND ML1,rv,0)) ml_s, SUM(IF(date BETWEEN ML0 AND ML1,rr,0)) ml_r, SUM(IF(date BETWEEN ML0 AND ML1,bl,0)) ml_b, COUNTIF(date BETWEEN ML0 AND ML1 AND rv>0) ml_n,
    SUM(IF(date BETWEEN Y0 AND D,rv,0)) y_s, SUM(IF(date BETWEEN Y0 AND D,rr,0)) y_r, SUM(IF(date BETWEEN Y0 AND D,bl,0)) y_b, COUNTIF(date BETWEEN Y0 AND D AND rv>0) y_n,
    SUM(IF(date BETWEEN YL0 AND ML1,rv,0)) yl_s, SUM(IF(date BETWEEN YL0 AND ML1,rr,0)) yl_r, SUM(IF(date BETWEEN YL0 AND ML1,bl,0)) yl_b, COUNTIF(date BETWEEN YL0 AND ML1 AND rv>0) yl_n
  FROM S s CROSS JOIN R GROUP BY s.store),
T  AS (SELECT t.store, SUM(IF(t.date=R.D,t.target,0)) dt, SUM(IF(t.date>=R.W0,t.target,0)) wt, SUM(t.target) mt FROM `rural-data-analystic.daily_sale_new_report.target` t, R WHERE t.date BETWEEN R.M0 AND R.D GROUP BY 1),
TY AS (SELECT y.store, SUM(y.target_ytd) ty FROM `rural-data-analystic.daily_sale_new_report.target_ytd` y, R WHERE y.month >= R.Y0 AND y.month < R.M0 GROUP BY 1),
LO AS (SELECT l.store, SUM(loss_value) lo FROM `rural-data-analystic.daily_sale_new_report.loss` l, R WHERE l.date BETWEEN R.M0 AND R.D GROUP BY 1),
SH AS (SELECT h.store, SUM(shrinkage_value) sh FROM `rural-data-analystic.daily_sale_new_report.shrinkage` h, R WHERE h.date BETWEEN R.M0 AND R.D GROUP BY 1),
K  AS (SELECT store FROM A UNION DISTINCT SELECT store FROM `rural-data-analystic.daily_sale_new_report.stock`)
SELECT K.store, A.* EXCEPT(store), T.dt, T.wt, T.mt, TY.ty, LO.lo, SH.sh, st.stock_value st, st.cogs_avg_30d cg,
       R.D rd, R.DL rdl
FROM K CROSS JOIN R
LEFT JOIN A USING(store) LEFT JOIN T USING(store) LEFT JOIN TY USING(store)
LEFT JOIN LO USING(store) LEFT JOIN SH USING(store)
LEFT JOIN `rural-data-analystic.daily_sale_new_report.stock` st USING(store)
