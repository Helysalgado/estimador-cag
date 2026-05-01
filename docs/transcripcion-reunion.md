# Transcripción de reunión (ejemplo para el ejercicio)

**Fecha:** (ejemplo) 15 de abril de 2026  
**Participantes:** Ana (cliente), Luis (técnico)

---

Ana: Necesitamos un portal interno para que el equipo de ventas registre oportunidades y pueda ver un pipeline simple por etapas. No tenemos CRM hoy; todo está en hojas de cálculo.

Luis: ¿Cuántos usuarios concurrentes aproximados?

Ana: Unos 25 vendedores en horario laboral, más 5 personas de operaciones que solo consultan reportes.

Luis: ¿Integraciones?

Ana: Quisiéramos exportar a CSV y, si se puede en una segunda fase, conectar con el correo para enviar recordatorios automáticos. También autenticación con la cuenta corporativa (SSO) sería ideal, pero podemos empezar con usuario y contraseña si el tiempo aprieta.

Luis: ¿Plazo?

Ana: Nos gustaría un MVP en **8 semanas** para probarlo con un piloto de un mes.

Luis: ¿Algún requisito de cumplimiento?

Ana: Datos en México, backups diarios y bitácora de quién cambió cada oportunidad.

---

*Este texto es ficticio y sirve como parámetro de práctica para `POST /api/v1/estimate`.*
