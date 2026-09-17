# AGENTS.md — Agent Instructions

> Este archivo es el punto de entrada de cada sesión.
> Léelo primero, siempre, antes de hacer cualquier otra cosa.

---

## Archivos de orquestación del proyecto — qué es cada uno

| Archivo | Propósito | Quién lo edita |
|---|---|---|
| `AGENTS.md` | Instrucciones del agente (este archivo) | Solo el humano |
| `PRODUCT_BACKLOG.md` | Lista de features y tareas pendientes — el backlog completo | Agente agrega, humano aprueba |
| `SPRINT_BACKLOG.md` | Lista detallada de tareas del Sprint actual | Agente agrega, humano aprueba |
| `SPRINT_TASK.md` | Tarea o actividad especifica dentro de un Sprint | Agente agrega, humano aprueba |
| `CHANGELOG.md` | Log permanente de decisiones y acciones tomadas — con el porqué | Agente solo agrega, nunca edita entradas pasadas |
| `SPECIFICATIONS.md` | Documento de especificación técnica y de diseño del proyecto | Agente solo agrega, nunca edita entradas pasadas |
| `PRD.md` | Documento de especificación de producto y requerimientos | Agente solo agrega, nunca edita entradas pasadas |
---

## Cómo leer el contexto al inicio de cada sesión

`AGENTS.md` → `SPRINT_BACKLOG.md` → `SPRINT_TASK.md` → `CHANGELOG.md`.

Si los archivos no existen es la primera sesión, entonces revisar `SPECIFICATIONS.md` y `PRD.md` para entender el contexto del proyecto.
Confirmar el objetivo del proyecto con el humano y crear el `PRODUCT_BACKLOG.md` inicial si no existe.
Crear el `SPRINT_BACKLOG.md` inicial con las tareas de la primera fase, y el `SPRINT_TASK.md` con la primera tarea a ejecutar.

---

## Cómo funciona PRODUCT_BACKLOG.md / SPRINT_BACKLOG.md / SPRINT_TASK.md / CHANGELOG.md

`PRODUCT_BACKLOG.md` contiene la lista completa de features y tareas pendientes del proyecto, con su prioridad y estado.
`SPRINT_BACKLOG.md` contiene la lista de tareas del Sprint actual, con su prioridad y estado.
`SPRINT_TASK.md` contiene la descripción de la tarea o actividad específica que se está ejecutando en el Sprint actual, con su prioridad y estado.
`CHANGELOG.md` contiene un log permanente de decisiones y acciones tomadas, con el porqué de cada decisión.

---

## Flujo de trabajo con Git

Rama `dev` de integración, un branch por fase (`<type>/<descripcion-corta>`), commits atómicos, merge `--no-ff` a `dev` al cerrar cada fase, `main` reservada para releases estables.

## Principios generales

- **Elaboración progresiva.** Las fases bloqueadas se documentan como tal, nunca se ocultan ni se simulan como completas.
- **Una fase a la vez.**
- **Preguntar antes de asumir.** Cualquier ambigüedad sobre el objetivo del proyecto, la prioridad de las tareas o el alcance de una fase debe ser consultada con el humano antes de continuar.
- **Los cambios son trazables** — cada decisión relevante va a `CHANGELOG.md`.
