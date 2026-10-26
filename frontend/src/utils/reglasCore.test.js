import { test } from 'node:test'
import assert from 'node:assert/strict'
import { progresoCotizaciones, mensajeCotizaciones, prioridadAutomatica } from './reglasCore.js'
const reglas={limite_caja_chica:'1000',umbral_cotizaciones:'500',cotizaciones_minimas:3,proveedores_distintos:true,categorias_prioridad:['RED','SERVIDORES'],palabras_prioridad:['red','conectividad de internet'],prioridad_automatica:'ALTA'}
const fila=(proveedor,proveedor_identificador='')=>({proveedor,proveedor_identificador,archivo_url:'/media/prueba.pdf'})
test('R02 calcula una y dos cotizaciones faltantes y respeta el umbral inclusivo',()=>{
  assert.deepEqual(progresoCotizaciones(700,[fila('Uno')],reglas),{requeridas:3,actuales:1,faltantes:2})
  const progreso=progresoCotizaciones(700,[fila('Uno'),fila('Dos')],reglas)
  assert.equal(progreso.faltantes,1)
  assert.match(mensajeCotizaciones(700,progreso,reglas),/agregar 1 cotización adicional/)
  assert.equal(progresoCotizaciones(500,[fila('Uno')],reglas).faltantes,0)
  assert.equal(progresoCotizaciones(700,[fila('Uno')],{...reglas,umbral_cotizaciones:'800'}).faltantes,0)
})
test('R02 no cuenta variantes de nombre o del mismo identificador como proveedores distintos',()=>{
  assert.equal(progresoCotizaciones(700,[fila('Ácme S.R.L.'),fila('acme srl'),fila(' ACME S R L ')],reglas).actuales,1)
  assert.equal(progresoCotizaciones(700,[fila('Nombre A','123-45'),fila('Alias A','12345')],reglas).actuales,1)
  assert.equal(progresoCotizaciones(700,[fila('Uno'),fila('Dos'),fila('Tres')],reglas).faltantes,0)
  assert.equal(progresoCotizaciones(700,[fila('')],reglas).actuales,0)
})
test('R03 evalúa categoría, título y descripción sin confundir pared con red',()=>{
  for(const texto of ['Falla de RED','Red del laboratorio','Sin conectividad de internet'])assert.equal(prioridadAutomatica(texto,'','',reglas),'ALTA')
  assert.equal(prioridadAutomatica('','Sin conectividad DE INTERNET','',reglas),'ALTA')
  assert.equal(prioridadAutomatica('Sin palabras clave','',{codigo:'SERVIDORES'},reglas),'ALTA')
  for(const texto of ['Pared dañada','Cambio de pintura','redimensionar'])assert.equal(prioridadAutomatica(texto,'','',reglas),null)
  assert.equal(prioridadAutomatica('Falla de red','','',reglas),'ALTA')
  assert.equal(prioridadAutomatica('Pared dañada','','',reglas),null)
})
