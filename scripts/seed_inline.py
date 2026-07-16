"""
Inline seed script — datos de mock embebidos directamente, sin archivos externos.
Usar en producción (Railway) donde el mock-generator no está disponible.

Local:   python scripts/seed_inline.py
Railway: python scripts/seed_inline.py  (via release command o one-off job)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.empresa import Empresa
from app.models.periodo import PeriodoFinanciero
from app.models.usuario import Usuario
from app.services.auth_service import hash_password

# ── Datos embebidos — generados desde finpyme-mock-generator/output/ ────────

MESES_SABORES = [{'periodo': '2025-01',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 21852331.72},
                              {'nombre': 'Domicilios', 'valor': 10257519.14},
                              {'nombre': 'Eventos y reservas', 'valor': 1121467.5}],
               'total': 33231318.35},
  'gastos': {'nomina': 7772689.16, 'proveedores': 7219991.11, 'arriendo': 3600000.0,
             'servicios': 1486332.75, 'otros': 1406280.05, 'total': 21485293.07},
  'utilidad_neta': 11746025.28, 'margen_pct': 35.35},
 {'periodo': '2025-02',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 14225824.59},
                              {'nombre': 'Domicilios', 'valor': 7903716.0},
                              {'nombre': 'Eventos y reservas', 'valor': 1111534.98}],
               'total': 23241075.56},
  'gastos': {'nomina': 5544384.19, 'proveedores': 5374284.35, 'arriendo': 3600000.0,
             'servicios': 986901.26, 'otros': 1129383.17, 'total': 16634952.96},
  'utilidad_neta': 6606122.6, 'margen_pct': 28.42,
  '_anomalia': {'tipo': 'ingreso_bajo', 'magnitud_pct': 39.0,
                'descripcion': 'Baja demanda prolongada: competencia nueva en el mismo bloque'}},
 {'periodo': '2025-03',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 25208495.92},
                              {'nombre': 'Domicilios', 'valor': 15401247.63},
                              {'nombre': 'Eventos y reservas', 'valor': 2929742.84}],
               'total': 43539486.4},
  'gastos': {'nomina': 10120206.42, 'proveedores': 10427778.56, 'arriendo': 3600000.0,
             'servicios': 2490880.4, 'otros': 1998731.59, 'total': 28637596.96},
  'utilidad_neta': 14901889.44, 'margen_pct': 34.23},
 {'periodo': '2025-04',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 33467717.74},
                              {'nombre': 'Domicilios', 'valor': 14998978.83},
                              {'nombre': 'Eventos y reservas', 'valor': 3993766.96}],
               'total': 52460463.53},
  'gastos': {'nomina': 12328479.73, 'proveedores': 15374233.8, 'arriendo': 3600000.0,
             'servicios': 3384736.69, 'otros': 3027054.98, 'total': 37714505.2},
  'utilidad_neta': 14745958.33, 'margen_pct': 28.11},
 {'periodo': '2025-05',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 31513611.54},
                              {'nombre': 'Domicilios', 'valor': 15545786.17},
                              {'nombre': 'Eventos y reservas', 'valor': 3844525.7}],
               'total': 50903923.42},
  'gastos': {'nomina': 12022191.35, 'proveedores': 14058518.03, 'arriendo': 3600000.0,
             'servicios': 3179662.84, 'otros': 2157517.8, 'total': 35017890.03},
  'utilidad_neta': 15886033.39, 'margen_pct': 31.21},
 {'periodo': '2025-06',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 27930334.56},
                              {'nombre': 'Domicilios', 'valor': 16307684.73},
                              {'nombre': 'Eventos y reservas', 'valor': 5036151.14}],
               'total': 49274170.44},
  'gastos': {'nomina': 12550185.73, 'proveedores': 11816641.39, 'arriendo': 3600000.0,
             'servicios': 3355250.2, 'otros': 2330639.44, 'total': 33652716.76},
  'utilidad_neta': 15621453.68, 'margen_pct': 31.7},
 {'periodo': '2025-07',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 30708926.94},
                              {'nombre': 'Domicilios', 'valor': 17049869.42},
                              {'nombre': 'Eventos y reservas', 'valor': 5456935.66}],
               'total': 53215732.02},
  'gastos': {'nomina': 12583807.64, 'proveedores': 13552419.73, 'arriendo': 3600000.0,
             'servicios': 3635858.5, 'otros': 2657749.45, 'total': 36029835.33},
  'utilidad_neta': 17185896.69, 'margen_pct': 32.29},
 {'periodo': '2025-08',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 25127357.92},
                              {'nombre': 'Domicilios', 'valor': 15178124.97},
                              {'nombre': 'Eventos y reservas', 'valor': 3390505.64}],
               'total': 43695988.53},
  'gastos': {'nomina': 10064016.21, 'proveedores': 10824567.67, 'arriendo': 3600000.0,
             'servicios': 3197752.67, 'otros': 1846252.76, 'total': 29532589.31},
  'utilidad_neta': 14163399.22, 'margen_pct': 32.41},
 {'periodo': '2025-09',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 28459537.14},
                              {'nombre': 'Domicilios', 'valor': 14379980.56},
                              {'nombre': 'Eventos y reservas', 'valor': 3912825.17}],
               'total': 46752342.87},
  'gastos': {'nomina': 10942825.59, 'proveedores': 12397749.32, 'arriendo': 3600000.0,
             'servicios': 2598238.2, 'otros': 2373870.07, 'total': 31912683.18},
  'utilidad_neta': 14839659.69, 'margen_pct': 31.74},
 {'periodo': '2025-10',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 29689770.41},
                              {'nombre': 'Domicilios', 'valor': 16392580.65},
                              {'nombre': 'Eventos y reservas', 'valor': 5707173.09}],
               'total': 51789524.15},
  'gastos': {'nomina': 12036267.31, 'proveedores': 11779500.98, 'arriendo': 3600000.0,
             'servicios': 2572683.32, 'otros': 2173957.13, 'total': 32162408.74},
  'utilidad_neta': 19627115.41, 'margen_pct': 37.9},
 {'periodo': '2025-11',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 33212908.59},
                              {'nombre': 'Domicilios', 'valor': 16544263.79},
                              {'nombre': 'Eventos y reservas', 'valor': 7048252.37}],
               'total': 56805424.75},
  'gastos': {'nomina': 13139460.52, 'proveedores': 14571309.94, 'arriendo': 3600000.0,
             'servicios': 3141376.24, 'otros': 3126302.57, 'total': 37578449.27},
  'utilidad_neta': 19226975.48, 'margen_pct': 33.85},
 {'periodo': '2025-12',
  'ingresos': {'categorias': [{'nombre': 'Ventas en restaurante', 'valor': 40953432.59},
                              {'nombre': 'Domicilios', 'valor': 17414713.93},
                              {'nombre': 'Eventos y reservas', 'valor': 10088385.56}],
               'total': 68456532.08},
  'gastos': {'nomina': 19335749.39, 'proveedores': 17562907.08, 'arriendo': 3600000.0,
             'servicios': 4431304.88, 'otros': 3698856.34, 'total': 48628817.68},
  'utilidad_neta': 19827714.4, 'margen_pct': 28.96}]

MESES_PROGRESO = [{'periodo': '2025-01',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 39479464.25},
                              {'nombre': 'Ventas al detal', 'valor': 15007353.26},
                              {'nombre': 'Servicios logísticos', 'valor': 9524752.88},
                              {'nombre': 'Otros ingresos', 'valor': 1660965.83}],
               'total': 65672536.22},
  'gastos': {'nomina': 17188737.83, 'proveedores': 8645788.52, 'arriendo': 7560000.0,
             'servicios': 4331877.59, 'otros': 5131005.58, 'total': 42857409.52},
  'utilidad_neta': 22815126.7, 'margen_pct': 34.74},
 {'periodo': '2025-02',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 42312184.47},
                              {'nombre': 'Ventas al detal', 'valor': 17922376.96},
                              {'nombre': 'Servicios logísticos', 'valor': 11464337.32},
                              {'nombre': 'Otros ingresos', 'valor': 1719506.75}],
               'total': 73418405.51},
  'gastos': {'nomina': 19006061.05, 'proveedores': 9926698.78, 'arriendo': 7560000.0,
             'servicios': 4810396.61, 'otros': 5735738.2, 'total': 47038894.64},
  'utilidad_neta': 26379510.87, 'margen_pct': 35.93},
 {'periodo': '2025-03',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 46343016.72},
                              {'nombre': 'Ventas al detal', 'valor': 19755018.5},
                              {'nombre': 'Servicios logísticos', 'valor': 11040553.45},
                              {'nombre': 'Otros ingresos', 'valor': 1846581.26}],
               'total': 78985169.93},
  'gastos': {'nomina': 20740394.99, 'proveedores': 11607469.7, 'arriendo': 7560000.0,
             'servicios': 6107993.25, 'otros': 5992488.47, 'total': 52008346.41},
  'utilidad_neta': 26976823.52, 'margen_pct': 34.15},
 {'periodo': '2025-04',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 48730699.1},
                              {'nombre': 'Ventas al detal', 'valor': 21594904.36},
                              {'nombre': 'Servicios logísticos', 'valor': 12377000.12},
                              {'nombre': 'Otros ingresos', 'valor': 2001112.55}],
               'total': 84703716.13},
  'gastos': {'nomina': 22129608.65, 'proveedores': 12372474.1, 'arriendo': 7560000.0,
             'servicios': 6364867.39, 'otros': 6472526.21, 'total': 54899476.36},
  'utilidad_neta': 29804239.77, 'margen_pct': 35.19},
 {'periodo': '2025-05',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 53383594.22},
                              {'nombre': 'Ventas al detal', 'valor': 24132049.4},
                              {'nombre': 'Servicios logísticos', 'valor': 11997814.28},
                              {'nombre': 'Otros ingresos', 'valor': 1514750.84}],
               'total': 91028208.73},
  'gastos': {'nomina': 24288813.24, 'proveedores': 14508277.12, 'arriendo': 7560000.0,
             'servicios': 7425585.28, 'otros': 6195702.01, 'total': 59978377.65},
  'utilidad_neta': 31049831.08, 'margen_pct': 34.11},
 {'periodo': '2025-06',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 51232177.36},
                              {'nombre': 'Ventas al detal', 'valor': 22444385.82},
                              {'nombre': 'Servicios logísticos', 'valor': 12888037.04},
                              {'nombre': 'Otros ingresos', 'valor': 1797686.17}],
               'total': 88362286.39},
  'gastos': {'nomina': 25249004.95, 'proveedores': 14023084.1, 'arriendo': 7560000.0,
             'servicios': 7008925.26, 'otros': 6563895.42, 'total': 60404909.73},
  'utilidad_neta': 27957376.66, 'margen_pct': 31.64},
 {'periodo': '2025-07',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 50721152.48},
                              {'nombre': 'Ventas al detal', 'valor': 19467914.07},
                              {'nombre': 'Servicios logísticos', 'valor': 12809973.17},
                              {'nombre': 'Otros ingresos', 'valor': 1578410.1}],
               'total': 84577449.83},
  'gastos': {'nomina': 21993045.7, 'proveedores': 12566696.5, 'arriendo': 7560000.0,
             'servicios': 7280936.19, 'otros': 5646242.07, 'total': 55046920.46},
  'utilidad_neta': 29530529.37, 'margen_pct': 34.92},
 {'periodo': '2025-08',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 54083512.23},
                              {'nombre': 'Ventas al detal', 'valor': 19949475.81},
                              {'nombre': 'Servicios logísticos', 'valor': 13264551.49},
                              {'nombre': 'Otros ingresos', 'valor': 1686055.97}],
               'total': 88983595.5},
  'gastos': {'nomina': 23713079.91, 'proveedores': 14152178.64, 'arriendo': 7560000.0,
             'servicios': 7364323.82, 'otros': 6240215.55, 'total': 59029797.92},
  'utilidad_neta': 29953797.58, 'margen_pct': 33.66},
 {'periodo': '2025-09',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 55104640.44},
                              {'nombre': 'Ventas al detal', 'valor': 25709434.8},
                              {'nombre': 'Servicios logísticos', 'valor': 13863890.24},
                              {'nombre': 'Otros ingresos', 'valor': 1449801.58}],
               'total': 96127767.05},
  'gastos': {'nomina': 24746155.98, 'proveedores': 15261159.08, 'arriendo': 7560000.0,
             'servicios': 7820622.71, 'otros': 7048861.33, 'total': 62436799.1},
  'utilidad_neta': 33690967.95, 'margen_pct': 35.05},
 {'periodo': '2025-10',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 60902415.97},
                              {'nombre': 'Ventas al detal', 'valor': 22840511.12},
                              {'nombre': 'Servicios logísticos', 'valor': 15202039.42},
                              {'nombre': 'Otros ingresos', 'valor': 1768670.97}],
               'total': 100713637.49},
  'gastos': {'nomina': 44727667.75, 'proveedores': 17635501.13, 'arriendo': 7560000.0,
             'servicios': 8710039.36, 'otros': 8605164.16, 'total': 87238372.41},
  'utilidad_neta': 13475265.08, 'margen_pct': 13.38,
  '_anomalia': {'tipo': 'contratacion_temporal', 'magnitud_pct': 69.7,
                'descripcion': 'Outsourcing cargue/descargue más equipo fijo: costo nómina '
                               'duplicado respecto a mes base'}},
 {'periodo': '2025-11',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 60487229.22},
                              {'nombre': 'Ventas al detal', 'valor': 21497120.02},
                              {'nombre': 'Servicios logísticos', 'valor': 16455002.06},
                              {'nombre': 'Otros ingresos', 'valor': 1589025.23}],
               'total': 100028376.53},
  'gastos': {'nomina': 26354058.15, 'proveedores': 17543988.61, 'arriendo': 7560000.0,
             'servicios': 9249911.65, 'otros': 8443316.67, 'total': 69151275.08},
  'utilidad_neta': 30877101.45, 'margen_pct': 30.87},
 {'periodo': '2025-12',
  'ingresos': {'categorias': [{'nombre': 'Ventas al por mayor', 'valor': 63838819.24},
                              {'nombre': 'Ventas al detal', 'valor': 25367684.66},
                              {'nombre': 'Servicios logísticos', 'valor': 16999826.81},
                              {'nombre': 'Otros ingresos', 'valor': 1388249.89}],
               'total': 107594580.6},
  'gastos': {'nomina': 33024212.69, 'proveedores': 14791325.1, 'arriendo': 7560000.0,
             'servicios': 9110170.54, 'otros': 8877136.25, 'total': 73362844.58},
  'utilidad_neta': 34231736.02, 'margen_pct': 31.82}]

MESES_VITALIA = [{'periodo': '2025-01',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 8200083.52},
                              {'nombre': 'Consultas médicas', 'valor': 5584076.51},
                              {'nombre': 'Productos y suplementos', 'valor': 2224318.19},
                              {'nombre': 'Membresías mensuales', 'valor': 2436097.75}],
               'total': 18444575.97},
  'gastos': {'nomina_medica_admin': 5297995.22, 'insumos_materiales': 1833929.49,
             'arriendo': 3240000.0, 'marketing_digital': 959694.32, 'otros': 814659.62,
             'total': 12146278.66},
  'utilidad_neta': 6298297.31, 'margen_pct': 34.15},
 {'periodo': '2025-02',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 10238791.97},
                              {'nombre': 'Consultas médicas', 'valor': 6117307.81},
                              {'nombre': 'Productos y suplementos', 'valor': 2788466.83},
                              {'nombre': 'Membresías mensuales', 'valor': 2083018.82}],
               'total': 21227585.42},
  'gastos': {'nomina_medica_admin': 6194497.59, 'insumos_materiales': 2416347.08,
             'arriendo': 3240000.0, 'marketing_digital': 972772.61, 'otros': 830921.26,
             'total': 13654538.54},
  'utilidad_neta': 7573046.88, 'margen_pct': 35.68},
 {'periodo': '2025-03',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 13336837.75},
                              {'nombre': 'Consultas médicas', 'valor': 6448605.75},
                              {'nombre': 'Productos y suplementos', 'valor': 3034283.16},
                              {'nombre': 'Membresías mensuales', 'valor': 2188475.67}],
               'total': 25008202.33},
  'gastos': {'nomina_medica_admin': 7466646.27, 'insumos_materiales': 3104260.81,
             'arriendo': 3240000.0, 'marketing_digital': 992240.92, 'otros': 1143526.72,
             'total': 15946674.72},
  'utilidad_neta': 9061527.61, 'margen_pct': 36.23},
 {'periodo': '2025-04',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 15624226.16},
                              {'nombre': 'Consultas médicas', 'valor': 7357215.69},
                              {'nombre': 'Productos y suplementos', 'valor': 3500346.36},
                              {'nombre': 'Membresías mensuales', 'valor': 2351295.72}],
               'total': 28833083.93},
  'gastos': {'nomina_medica_admin': 8585531.4, 'insumos_materiales': 3637621.5,
             'arriendo': 3240000.0, 'marketing_digital': 1778719.18, 'otros': 1189288.81,
             'total': 18431160.89},
  'utilidad_neta': 10401923.04, 'margen_pct': 36.08},
 {'periodo': '2025-05',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 18573735.68},
                              {'nombre': 'Consultas médicas', 'valor': 7071175.59},
                              {'nombre': 'Productos y suplementos', 'valor': 3936038.15},
                              {'nombre': 'Membresías mensuales', 'valor': 2427232.67}],
               'total': 32008182.09},
  'gastos': {'nomina_medica_admin': 8987574.72, 'insumos_materiales': 4740393.11,
             'arriendo': 3240000.0, 'marketing_digital': 2526532.41, 'otros': 1549017.17,
             'total': 21043517.41},
  'utilidad_neta': 10964664.68, 'margen_pct': 34.26},
 {'periodo': '2025-06',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 28600724.55},
                              {'nombre': 'Consultas médicas', 'valor': 8511059.34},
                              {'nombre': 'Productos y suplementos', 'valor': 4782293.06},
                              {'nombre': 'Membresías mensuales', 'valor': 2564154.23}],
               'total': 44458231.17},
  'gastos': {'nomina_medica_admin': 13544661.52, 'insumos_materiales': 9117861.27,
             'arriendo': 3240000.0, 'marketing_digital': 1691028.35, 'otros': 1925832.9,
             'total': 29519384.05},
  'utilidad_neta': 14938847.12, 'margen_pct': 33.6},
 {'periodo': '2025-07',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 18894862.04},
                              {'nombre': 'Consultas médicas', 'valor': 7463899.49},
                              {'nombre': 'Productos y suplementos', 'valor': 4275081.61},
                              {'nombre': 'Membresías mensuales', 'valor': 2538541.86}],
               'total': 33172385.02},
  'gastos': {'nomina_medica_admin': 9566323.34, 'insumos_materiales': 4964450.64,
             'arriendo': 3240000.0, 'marketing_digital': 1035430.3, 'otros': 1427422.75,
             'total': 20233627.03},
  'utilidad_neta': 12938757.99, 'margen_pct': 39.0},
 {'periodo': '2025-08',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 14204691.39},
                              {'nombre': 'Consultas médicas', 'valor': 7315598.97},
                              {'nombre': 'Productos y suplementos', 'valor': 3157083.13},
                              {'nombre': 'Membresías mensuales', 'valor': 2440080.12}],
               'total': 27117453.62},
  'gastos': {'nomina_medica_admin': 7766739.06, 'insumos_materiales': 3179365.76,
             'arriendo': 3240000.0, 'marketing_digital': 1133818.35, 'otros': 1140636.96,
             'total': 16460560.13},
  'utilidad_neta': 10656893.49, 'margen_pct': 39.3},
 {'periodo': '2025-09',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 16554305.33},
                              {'nombre': 'Consultas médicas', 'valor': 6868215.35},
                              {'nombre': 'Productos y suplementos', 'valor': 3439246.9},
                              {'nombre': 'Membresías mensuales', 'valor': 2407027.37}],
               'total': 29268794.94},
  'gastos': {'nomina_medica_admin': 8625223.56, 'insumos_materiales': 3967436.25,
             'arriendo': 3240000.0, 'marketing_digital': 1741843.11, 'otros': 1312263.84,
             'total': 18886766.77},
  'utilidad_neta': 10382028.17, 'margen_pct': 35.47},
 {'periodo': '2025-10',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 17676739.67},
                              {'nombre': 'Consultas médicas', 'valor': 7670710.65},
                              {'nombre': 'Productos y suplementos', 'valor': 3670165.09},
                              {'nombre': 'Membresías mensuales', 'valor': 2523373.72}],
               'total': 31540989.13},
  'gastos': {'nomina_medica_admin': 8891589.45, 'insumos_materiales': 4901277.59,
             'arriendo': 3240000.0, 'marketing_digital': 2796195.76, 'otros': 1439782.0,
             'total': 21268844.8},
  'utilidad_neta': 10272144.33, 'margen_pct': 32.57},
 {'periodo': '2025-11',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 25464706.42},
                              {'nombre': 'Consultas médicas', 'valor': 8024043.61},
                              {'nombre': 'Productos y suplementos', 'valor': 5004524.35},
                              {'nombre': 'Membresías mensuales', 'valor': 2737517.6}],
               'total': 41230792.0},
  'gastos': {'nomina_medica_admin': 13013040.44, 'insumos_materiales': 8789223.92,
             'arriendo': 3240000.0, 'marketing_digital': 1960904.36, 'otros': 2323016.75,
             'total': 29326185.47},
  'utilidad_neta': 11904606.53, 'margen_pct': 28.87},
 {'periodo': '2025-12',
  'ingresos': {'categorias': [{'nombre': 'Procedimientos estéticos', 'valor': 27801030.54},
                              {'nombre': 'Consultas médicas', 'valor': 7548869.01},
                              {'nombre': 'Productos y suplementos', 'valor': 4422764.03},
                              {'nombre': 'Membresías mensuales', 'valor': 2935448.6}],
               'total': 42708112.18},
  'gastos': {'nomina_medica_admin': 15082040.67, 'insumos_materiales': 8660449.24,
             'arriendo': 3240000.0, 'marketing_digital': 1465979.46, 'otros': 2392112.72,
             'total': 30840582.09},
  'utilidad_neta': 11867530.09, 'margen_pct': 27.79}]

# ── Configuración del seed ───────────────────────────────────────────────────

SEED_DATA = [
    {
        "empresa": {
            "nombre": "Sabores de la Abuela S.A.S.",
            "nit": "901.234.567-1",
            "ciudad": "Bogotá",
            "sector": "restaurante",
        },
        "usuario": {
            "email": "demo@sabores.com",
            "password": "demo1234",
            "nombre": "Demo Sabores",
            "rol": "owner",
        },
        "meses": MESES_SABORES,
    },
    {
        "empresa": {
            "nombre": "Distribuidora El Progreso S.A.S.",
            "nit": "900.123.456-7",
            "ciudad": "Medellín",
            "sector": "distribuidora",
        },
        "usuario": {
            "email": "demo@progreso.com",
            "password": "demo1234",
            "nombre": "Demo Progreso",
            "rol": "owner",
        },
        "meses": MESES_PROGRESO,
    },
    {
        "empresa": {
            "nombre": "Clínica Estética Vitalia S.A.S.",
            "nit": "900.987.654-3",
            "ciudad": "Cali",
            "sector": "clinica",
        },
        "usuario": {
            "email": "demo@vitalia.com",
            "password": "demo1234",
            "nombre": "Demo Vitalia",
            "rol": "owner",
        },
        "meses": MESES_VITALIA,
    },
]

# ── Lógica del seed ──────────────────────────────────────────────────────────

async def _delete_empresa(session: AsyncSession, nit: str) -> None:
    try:
        result = await session.execute(select(Empresa).where(Empresa.nit == nit))
    except Exception:
        await session.rollback()
        return
    empresa = result.scalar_one_or_none()
    if empresa is None:
        return
    await session.execute(
        delete(PeriodoFinanciero).where(PeriodoFinanciero.empresa_id == empresa.id)
    )
    await session.execute(delete(Usuario).where(Usuario.empresa_id == empresa.id))
    await session.execute(delete(Empresa).where(Empresa.id == empresa.id))


async def re_hash_passwords(factory) -> None:
    demo_passwords = {e["usuario"]["email"]: e["usuario"]["password"] for e in SEED_DATA}
    async with factory() as session:
        result = await session.execute(
            select(Usuario).where(Usuario.email.in_(demo_passwords))
        )
        usuarios = result.scalars().all()
        for usuario in usuarios:
            usuario.password_hash = hash_password(demo_passwords[usuario.email])
        await session.commit()
    print(f"  Passwords re-hasheados: {len(usuarios)} usuarios.")


async def seed() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    results = []

    async with factory() as session:
        print("Limpiando datos previos...")
        for entry in SEED_DATA:
            await _delete_empresa(session, entry["empresa"]["nit"])
        await session.commit()

        print("Insertando datos de demo...")
        for entry in SEED_DATA:
            empresa = Empresa(**entry["empresa"])
            session.add(empresa)
            await session.flush()

            u = entry["usuario"]
            session.add(
                Usuario(
                    empresa_id=empresa.id,
                    email=u["email"],
                    password_hash=hash_password(u["password"]),
                    nombre=u["nombre"],
                    rol=u["rol"],
                )
            )

            for mes in entry["meses"]:
                session.add(
                    PeriodoFinanciero(
                        empresa_id=empresa.id,
                        periodo=mes["periodo"],
                        datos_json=mes,
                        fuente="mock",
                    )
                )

            results.append(
                {
                    "nombre": entry["empresa"]["nombre"],
                    "email": u["email"],
                    "password": u["password"],
                    "periodos": len(entry["meses"]),
                }
            )

        await session.commit()

    await re_hash_passwords(factory)
    await engine.dispose()

    col = (32, 26, 12, 9)
    sep = "─" * (sum(col) + len(col) * 3 + 1)
    print(f"\n{sep}")
    print(
        f"  {'Empresa':<{col[0]}} {'Email':<{col[1]}} {'Password':<{col[2]}} {'Periodos':>{col[3]}}"
    )
    print(sep)
    for r in results:
        nombre = r["nombre"] if len(r["nombre"]) <= col[0] else r["nombre"][: col[0] - 2] + ".."
        print(
            f"  {nombre:<{col[0]}} {r['email']:<{col[1]}} {r['password']:<{col[2]}} {r['periodos']:>{col[3]}}"
        )
    print(sep)
    print(f"  Seed completado: {len(results)} empresas insertadas.\n")


if __name__ == "__main__":
    asyncio.run(seed())
