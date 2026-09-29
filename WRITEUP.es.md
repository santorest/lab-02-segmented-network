# Red segmentada para pymes con OPNsense

> **Resumen** — Diseño de referencia para una empresa ficticia de 40 personas con sede principal y una
> sucursal: cinco zonas de seguridad detrás de un firewall OPNsense con denegación por defecto, IPS Suricata,
> filtrado DNS, un túnel IPsec entre sedes con certificados, acceso remoto con TOTP y administración
> endurecida. La política del firewall se escribe una sola vez como código y de ella salen tanto la
> documentación como un verificador de conectividad automatizado e inofensivo.
> **Entregable: diseño de referencia, listo para construir.**

| | |
|---|---|
| **Rol asumido** | Ingeniero de redes y seguridad de una empresa de 40 personas con dos sedes |
| **Entorno** | Proxmox VE, dos firewalls OPNsense 26.7, bridges con VLAN, laboratorio aislado |
| **Herramientas** | OPNsense, Suricata, Unbound, IPsec (IKEv2), OpenVPN, Python |
| **Entregable** | Arquitectura, política como código (38 flujos probados), guías de configuración, herramientas de validación probadas |

---

## 1. Problema

- **Contexto:** una empresa ficticia de servicios profesionales, 40 empleados en tres áreas, una sede
  principal, una sucursal y un sitio web público. Hoy todo está en una única red plana.
- **Por qué importa:** en una red plana, un portátil infectado puede llegar a todos los servidores, a las copias
  de seguridad y a la página de administración del propio firewall. Los invitados del Wi-Fi también comparten
  esa red.
- **Requisitos:**
    1. El personal accede a internet y solo a los servicios internos que necesita.
    2. Los invitados solo acceden a internet.
    3. El sitio web es lo único accesible desde internet.
    4. Una estación o un servidor web comprometidos no pueden llegar a interfaces de administración ni a otras zonas.
    5. La sucursal usa los servicios de la sede por un túnel cifrado; el personal remoto se conecta con MFA.
    6. La administración solo se hace desde una red dedicada, con MFA, y toda decisión queda registrada de forma central.
- **Restricciones:** herramientas libres y de código abierto; laboratorio aislado; direcciones de rangos
  privados y de documentación.
- **Criterios de éxito:** cada flujo de la política se comporta según el diseño al probarlo desde dentro de cada
  zona, y las verificaciones manuales (cifrado del túnel, MFA, IPS, filtrado DNS) se superan.

## 2. Arquitectura

| Sede | Zona | VLAN | Subred | Propósito |
|---|---|---|---|---|
| Sede principal | SERVERS | 20 | 10.10.20.0/24 | Controlador de dominio, servidor Linux, SIEM Wazuh (Lab 01) |
| Sede principal | USERS | 30 | 10.10.30.0/24 | Estaciones del personal |
| Sede principal | GUEST | 40 | 10.10.40.0/24 | Wi-Fi de invitados, solo internet |
| Sede principal | DMZ | 50 | 10.10.50.0/24 | Servidor web público, sin acceso hacia dentro |
| Sede principal | MGMT | 99 | 10.10.99.0/24 | GUI/SSH del firewall y host de salto de administración |
| Sucursal | BR-USERS / BR-MGMT | 30 / 99 | 10.20.30.0/24, 10.20.99.0/24 | Personal de la sucursal y gestión de su firewall |
| — | WAN | — | 203.0.113.0/24 | Internet simulado (rango de documentación RFC 5737) |

El plan de direccionamiento completo y cada flujo probado con su justificación se generan desde la política:
[docs/ip-plan.md](docs/ip-plan.md) y [docs/rules.md](docs/rules.md).

| Decisión | Alternativas consideradas | Por qué esta |
|---|---|---|
| OPNsense 26.7 | Prueba de FortiGate-VM; pfSense CE | La prueba gratuita de FortiGate-VM solo permite 3 interfaces, 3 políticas y 3 rutas y no recibe actualizaciones de FortiGuard; OPNsense trae IPS, IPsec, OpenVPN y TOTP sin límites |
| Política como código (YAML) | Reglas documentadas a mano | Una sola fuente para las tablas de reglas y las pruebas; documentación y validación no pueden desalinearse |
| IPsec IKEv2 con certificados | Clave precompartida; WireGuard | Identidad y revocación por equipo; IKEv2 es lo que hablan la mayoría de firewalls corporativos |
| OpenVPN + TOTP | WireGuard | Doble factor integrado en OPNsense; WireGuard no tiene MFA nativo |
| Los clientes del dominio resuelven por dc01 → resolvedor filtrado del firewall | Clientes directo al firewall | Active Directory necesita el controlador de dominio para DNS; el filtrado se aplica igual a todo nombre externo |

## 3. Construcción

Guías paso a paso para OPNsense 26.7 en [docs/opnsense/](docs/opnsense/) (en inglés):

1. [Instalación e interfaces](docs/opnsense/01-install-and-interfaces.md): bridges de Proxmox, VLAN, direccionamiento.
2. [Reglas del firewall](docs/opnsense/02-firewall-rules.md): alias y una regla por flujo permitido, con bloqueo
   registrado al final de cada zona.
3. [NAT y salida](docs/opnsense/03-nat-and-egress.md): un solo servicio publicado; servidores y MGMT sin acceso
   directo a internet.
4. [IPS Suricata](docs/opnsense/04-ips-suricata.md): reglas ET Open; solo se bloquean firmas de alta confianza.
5. [Filtrado DNS](docs/opnsense/05-dns-filtering.md): listas de bloqueo en Unbound; los clientes no pueden
   saltarse el resolvedor.
6. [IPsec entre sedes](docs/opnsense/06-ipsec-site-to-site.md): cada parámetro con su motivo.
7. [OpenVPN + TOTP](docs/opnsense/07-openvpn-totp.md): certificado + contraseña + código de un solo uso.
8. [Endurecimiento de la administración](docs/opnsense/08-admin-hardening.md): GUI/SSH solo desde MGMT, MFA,
   registros hacia Wazuh, copias de seguridad cifradas.

## 4. Plan de validación

- **Verificación automática de conectividad** ([docs/validation.md](docs/validation.md)): desde un host de prueba
  en cada zona, `python3 -m labtools.checker --zone <ZONA>` prueba los 38 flujos de la política con conexiones
  TCP y ecos UDP normales hacia los propios hosts del laboratorio, y marca cada uno como *PASS*,
  *FAIL (blocked)* o *FAIL (allowed)*.
- **Verificaciones manuales** ([tests/test-plan.md](tests/test-plan.md)): el tráfico IPsec va cifrado en la red,
  el inicio de sesión VPN falla sin el código TOTP, el IPS alerta ante una firma de prueba inofensiva, los
  dominios bloqueados no resuelven y un inicio de sesión fallido en el firewall llega a Wazuh.

## 5. Entregables y medición

**Entregado en este repositorio:**

- Arquitectura, diseño de zonas y plan de direccionamiento para dos sedes.
- Una matriz de 38 flujos, cada uno con su justificación escrita, validada en CI (zonas desconocidas, flujos
  dentro de una misma zona, duplicados o justificaciones faltantes hacen fallar la compilación).
- Ocho guías de configuración de OPNsense y una guía para publicar configuraciones sin secretos.
- Un verificador de conectividad y un listener de destino cubiertos por pruebas automatizadas (incluidas sondas
  TCP/UDP reales), más una comprobación en CI de que la documentación generada coincide con la política.

**Cómo se miden los resultados:**

| Métrica | Definición |
|---|---|
| Conformidad con la política | Flujos que se comportaron según el diseño ÷ flujos probados, por zona y en total |
| Verificaciones manuales | Aprobado/fallido para cada verificación del plan de pruebas |

## 6. Lecciones de diseño y hoja de ruta

- **Revisa los límites de licencia antes de elegir un producto.** La prueba de FortiGate-VM parecía la opción
  obvia, pero no admitía ni el diseño básico de zonas; revisarlo primero evitó construir sobre un callejón sin
  salida.
- **Escribe la política una sola vez.** Tener zonas y flujos en un solo archivo YAML, del que salen la
  documentación y el verificador, elimina la desalineación habitual entre "lo que dice el diagrama" y "lo que
  hace el firewall".
- **Prueba las denegaciones, no solo los permisos.** Una política de denegación por defecto solo queda
  demostrada cuando los flujos bloqueados se prueban desde dentro de cada zona; por eso la política los lista
  explícitamente.
- **Las sondas necesitan que alguien responda.** Un flujo permitido hacia un puerto sin servicio se ve igual que
  uno bloqueado; por eso el diseño incluye un listener y marca los hosts cuyos servicios reales ya responden.
- **Diseñar para clientes reales cambia los detalles.** Los equipos unidos al dominio necesitan el controlador
  de dominio para DNS y los agentes del Lab 01 necesitan sus propios flujos; ambas cosas aparecieron solo al
  escribir las guías paso a paso.

**Hoja de ruta:** construir ambos firewalls con las guías, ejecutar el verificador desde las seis zonas y las
verificaciones manuales, publicar aquí la conformidad medida y, más adelante, comparar con un FortiGate con
licencia usando la misma política.

## 7. Reprodúcelo tú mismo

- Clonar: `git clone https://github.com/santorest/lab-02-segmented-network.git`
- Descargar el paquete: desde el sitio del portafolio (el SHA-256 aparece junto a la descarga).
- Tiempo estimado: 1–2 días.
- Limpieza: elimina las VM y los bridges; no se usan recursos en la nube.

## 8. Mapeo

| Control | Marco | Cómo lo aborda este proyecto |
|---|---|---|
| 13.4 Filtrar el tráfico entre segmentos de red | CIS Controls v8 | Firewall por zonas con denegación por defecto y una lista de permisos justificada y probada |
| 12.2 Establecer y mantener una arquitectura de red segura | CIS Controls v8 | Zonas segmentadas, DMZ, aislamiento de invitados, MGMT dedicada |
| 12.8 Recursos de cómputo dedicados para tareas administrativas | CIS Controls v8 | Zona MGMT y host de salto; GUI/SSH ligados a MGMT |
| 6.4 Exigir MFA para el acceso remoto a la red | CIS Controls v8 | OpenVPN con TOTP |
| 13.3 Desplegar una solución de detección de intrusiones en red | CIS Controls v8 | IPS Suricata en WAN y USERS |
| PR.IR-01 Las redes y entornos están protegidos contra accesos lógicos no autorizados | NIST CSF 2.0 | Zonas, control de salida, política probada |

---

*Todas las pruebas se realizan en un entorno de laboratorio aislado de mi propiedad. No se incluyen datos,
nombres de host ni configuraciones de ninguna organización real.*
