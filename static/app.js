const DAYS = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta"];
const PERIODS = ["1a aula", "2a aula", "3a aula", "4a aula", "5a aula"];

let state = null;
let validation = { conflicts: [], pendencies: [], warnings: [], score: 0 };
let currentView = "dashboard";
let gradeMode = "class";

const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => Array.from(parent.querySelectorAll(selector));
const id = () => Math.random().toString(16).slice(2, 14);
const csvToList = (value) => String(value || "").split(",").map((item) => item.trim()).filter(Boolean);
const listToCsv = (items) => (items || []).join(", ");

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

async function load() {
  const payload = await api("/api/state");
  state = payload.data;
  validation = payload.validation;
  render();
}

async function save() {
  const payload = await api("/api/state", { method: "POST", body: JSON.stringify(state) });
  state = payload.data;
  validation = payload.validation;
  render();
}

async function generate() {
  const payload = await api("/api/generate", { method: "POST", body: "{}" });
  state = payload.data;
  validation = payload.validation;
  render();
}

async function resetExample() {
  const confirmed = confirm("Restaurar os dados de exemplo? Os dados atuais serao substituidos.");
  if (!confirmed) return;
  const payload = await api("/api/reset", { method: "POST", body: "{}" });
  state = payload.data;
  validation = payload.validation;
  render();
}

function nameOf(collection, itemId, fallback = "") {
  return state[collection].find((item) => item.id === itemId)?.name || fallback;
}

function schoolDays() {
  return state?.school?.days?.length ? state.school.days : DAYS;
}

function activePeriods() {
  const periods = state?.school?.shifts?.flatMap((shift) => shift.periods || []) || PERIODS;
  return [...new Set(periods.length ? periods : PERIODS)];
}

function periodsForClass(schoolClass) {
  const shift = state.school.shifts.find((item) => item.id === schoolClass?.shift);
  return shift?.periods?.length ? shift.periods : activePeriods();
}

function render() {
  $("#schoolName").textContent = state.school.name || "Escola sem nome";
  $("#schoolYear").textContent = `Ano letivo ${state.school.year || ""}`;
  $("#score").textContent = validation.score ?? 0;
  renderDashboard();
  renderCadastros();
  renderMatriz();
  renderDisponibilidade();
  renderGrade();
  renderRelatorios();
}

function renderDashboard() {
  $("#dashboard").innerHTML = `
    <div class="grid three">
      ${metric("Professores", state.teachers.length)}
      ${metric("Turmas", state.classes.length)}
      ${metric("Aulas geradas", state.lessons.length)}
    </div>
    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><h3>Status da base funcional</h3><span class="chip">Fase 1 concluida</span></div>
      <div class="chips">
        <span class="chip">Servidor local</span>
        <span class="chip">Persistencia JSON</span>
        <span class="chip">Dados de exemplo</span>
        <span class="chip">Geracao inicial</span>
      </div>
      <p class="muted">Ultima gravacao: ${state.updatedAt || "ainda nao informada"}</p>
    </div>
    ${qualityPanel()}
    <div class="grid two" style="margin-top:16px">
      <div class="panel">
        <div class="panel-head"><h3>Alertas obrigatorios</h3><span class="chip">${validation.conflicts.length}</span></div>
        <div class="list">${alertList(validation.conflicts, "danger")}</div>
      </div>
      <div class="panel">
        <div class="panel-head"><h3>Pendencias e preferencias</h3><span class="chip">${validation.pendencies.length + validation.warnings.length}</span></div>
        <div class="list">${alertList([...validation.pendencies, ...validation.warnings])}</div>
      </div>
    </div>
    <div class="panel" style="margin-top:16px">
      <h3>Fases de elaboracao</h3>
      <div class="list" style="margin-top:12px">
        ${phase("1", "Base funcional", "Aplicacao abre, salva dados, restaura exemplo e gera uma grade inicial.")}
        ${phase("2", "Cadastros completos", "Escola, professores, turmas, disciplinas, salas, turnos e periodos configuraveis.")}
        ${phase("3", "Regras obrigatorias", "Conflitos obrigatorios validados no backend e exibidos na grade.")}
        ${phase("4", "Gerador robusto", "Melhorar algoritmo, pontuacao e distribuicao semanal.")}
        ${phase("5", "Ajuste manual seguro", "Inserir, mover, fixar e trocar aulas com controle de conflito.")}
        ${phase("6", "Visualizacoes", "Consolidar visoes por turma, professor, sala, geral, conflitos e pendencias.")}
        ${phase("7", "Relatorios", "PDF, CSV/Excel e relatorios por publico.")}
      </div>
    </div>
  `;
}

function qualityPanel() {
  const quality = validation.quality;
  if (!quality) {
    return `
      <div class="panel" style="margin-top:16px">
        <div class="panel-head"><h3>Gerador automatico</h3><span class="chip">Aguardando geracao</span></div>
        <p class="muted">Clique em "Gerar horario" para calcular pontuacao detalhada, tentativas e qualidade.</p>
      </div>`;
  }
  return `
    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><h3>Gerador automatico</h3><span class="chip">Tentativa ${quality.attempt}/${quality.maxAttempts}</span></div>
      <div class="chips">
        <span class="chip">Pontuacao ${quality.score}</span>
        <span class="chip">Fixadas ${quality.fixedLessons}</span>
        <span class="chip">Janelas ${quality.teacherWindows}</span>
        <span class="chip">Distribuicao ${quality.distributionPenalty}</span>
      </div>
    </div>`;
}

function metric(label, value) {
  return `<div class="panel metric"><span class="muted">${label}</span><strong>${value}</strong></div>`;
}

function phase(number, title, text) {
  return `<div class="item"><div><strong>Fase ${number}: ${title}</strong><p class="muted">${text}</p></div></div>`;
}

function alertList(items, type = "") {
  if (!items.length) return `<p class="muted">Nenhum item encontrado.</p>`;
  return items
    .map((item) => `<div class="alert ${type}"><strong>${item.message}</strong>${item.context ? `<p>${item.context}</p>` : ""}</div>`)
    .join("");
}

function conflictsForLesson(lessonId) {
  return validation.conflicts.filter((item) => item.lessonId === lessonId);
}

function renderCadastros() {
  $("#cadastros").innerHTML = `
    <div class="grid two">
      ${collectionPanel("Escola", "school")}
      ${collectionPanel("Professores", "teachers")}
      ${collectionPanel("Turmas", "classes")}
      ${collectionPanel("Disciplinas", "subjects")}
      ${collectionPanel("Salas e ambientes", "rooms")}
      ${turnosPanel()}
    </div>
  `;
}

function collectionPanel(title, key) {
  if (key === "school") {
    return `
      <div class="panel">
        <div class="panel-head"><h3>${title}</h3><button data-edit-school>Editar</button></div>
        <p><strong>${state.school.name}</strong></p>
        <p class="muted">${state.school.address || "Endereco nao informado"} | ${state.school.year}</p>
        <div class="chips">
          ${(state.school.days || DAYS).map((day) => `<span class="chip">${day}</span>`).join("")}
        </div>
      </div>`;
  }
  return `
    <div class="panel">
      <div class="panel-head"><h3>${title}</h3><button data-add="${key}">Adicionar</button></div>
      <div class="list">
        ${state[key]
          .map(
            (item) => `
            <div class="item">
              <div><strong>${item.name}</strong><p class="muted">${describeItem(key, item)}</p></div>
              <div class="actions"><button data-edit="${key}:${item.id}">Editar</button><button data-delete="${key}:${item.id}">Remover</button></div>
            </div>`
          )
          .join("") || `<p class="muted">Nenhum cadastro.</p>`}
      </div>
    </div>`;
}

function describeItem(key, item) {
  if (key === "teachers") {
    const subjects = (item.subjects || []).map((subjectId) => nameOf("subjects", subjectId)).filter(Boolean).join(", ") || "sem disciplinas";
    return `${item.contact || "Sem contato"} | ${subjects} | limite ${item.maxPerDay || "-"} aulas/dia`;
  }
  if (key === "classes") return `${item.grade || ""} | ${item.shift || "manha"} | ${item.students || 0} alunos | ${nameOf("rooms", item.defaultRoomId, "sem sala")}`;
  if (key === "subjects") return `${item.weeklyLoad || 0} aulas/semana | ${item.requireDouble ? "aula dupla obrigatoria" : "aula simples"}${item.requiredRoomType ? ` | ${item.requiredRoomType}` : ""}`;
  if (key === "rooms") {
    const compatible = (item.compatibleSubjects || []).map((subjectId) => nameOf("subjects", subjectId)).filter(Boolean).join(", ");
    return `${item.type || "Sala"} | capacidade ${item.capacity || 0}${compatible ? ` | ${compatible}` : ""}`;
  }
  return "";
}

function turnosPanel() {
  return `
    <div class="panel">
      <div class="panel-head"><h3>Turnos e periodos</h3><button data-edit-shifts>Editar</button></div>
      <div class="list">
        ${state.school.shifts
          .map((shift) => `<div class="item"><div><strong>${shift.name}</strong><p class="muted">${shift.id} | ${shift.periods.map(periodLabel).join(", ")}</p></div></div>`)
          .join("")}
      </div>
    </div>`;
}

function periodLabel(period) {
  const time = state.school.periodTimes?.[period];
  return time ? `${period} (${time.start}-${time.end})` : period;
}

function renderMatriz() {
  $("#matriz").innerHTML = `
    <div class="panel">
      <div class="panel-head"><h3>Matriz curricular</h3><button data-add-curriculum>Adicionar vinculo</button></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Turma</th><th>Disciplina</th><th>Professor</th><th>Aulas</th><th>Aula dupla</th><th>Sala especial</th><th></th></tr></thead>
          <tbody>
            ${state.curriculum
              .map(
                (row) => `<tr>
                  <td>${nameOf("classes", row.classId)}</td>
                  <td>${nameOf("subjects", row.subjectId)}</td>
                  <td>${nameOf("teachers", row.teacherId)}</td>
                  <td>${row.weeklyLessons}</td>
                  <td>${row.requiresDouble ? "Sim" : "Nao"}</td>
                  <td>${nameOf("rooms", row.specialRoomId, "-")}</td>
                  <td><button data-edit-curriculum="${row.id}">Editar</button></td>
                </tr>`
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </div>`;
}

function renderDisponibilidade() {
  $("#disponibilidade").innerHTML = `
    <div class="grid">
      ${state.teachers
        .map(
          (teacher) => `
          <div class="panel">
            <div class="panel-head"><h3>${teacher.name}</h3><span class="muted">Clique para bloquear/liberar</span></div>
            ${availabilityGrid(teacher)}
          </div>`
        )
        .join("")}
    </div>`;
}

function availabilityGrid(teacher) {
  return `
    <div class="availability-grid">
      <strong>Periodo</strong>${schoolDays().map((day) => `<strong>${day}</strong>`).join("")}
      ${activePeriods().map(
        (period) => `
          <span>${period}</span>
          ${schoolDays().map((day) => {
            const blocked = teacher.availability?.[day]?.[period] === "blocked";
            return `<button class="${blocked ? "blocked" : ""}" data-avail="${teacher.id}:${day}:${period}">${blocked ? "Bloqueado" : "Livre"}</button>`;
          }).join("")}`
      ).join("")}
    </div>`;
}

function renderGrade() {
  const activeCollection = gradeMode === "teacher" ? "teachers" : gradeMode === "room" ? "rooms" : "classes";
  const previousFilter = $("#gradeFilter")?.value;
  const selected = previousFilter || state[activeCollection][0]?.id || "";
  const title = gradeMode === "teacher" ? "Grade por professor" : gradeMode === "room" ? "Grade por sala" : gradeMode === "general" ? "Grade geral" : "Grade por turma";
  $("#grade").innerHTML = `
    <div class="panel no-print">
      <div class="panel-head"><h3>${title}</h3><button data-add-lesson>Inserir aula</button></div>
      <div class="tabs">
        <button class="${gradeMode === "class" ? "active" : ""}" data-grade-mode="class">Turma</button>
        <button class="${gradeMode === "teacher" ? "active" : ""}" data-grade-mode="teacher">Professor</button>
        <button class="${gradeMode === "room" ? "active" : ""}" data-grade-mode="room">Sala</button>
        <button class="${gradeMode === "general" ? "active" : ""}" data-grade-mode="general">Geral</button>
      </div>
      ${
        gradeMode === "general"
          ? `<p class="muted">Visao consolidada de todas as aulas por dia e periodo.</p>`
          : `<label>${title.replace("Grade por ", "")}<select id="gradeFilter">${state[activeCollection]
              .map((item) => `<option value="${item.id}">${item.name}</option>`)
              .join("")}</select></label>`
      }
    </div>
    <div style="height:16px"></div>
    ${gradeMode === "general" ? generalTimetable() : selected ? entityTimetable(gradeMode, selected) : `<p class="muted">Cadastre itens para montar a grade.</p>`}
  `;
  const filter = $("#gradeFilter");
  if (filter) {
    filter.value = selected;
    filter.addEventListener("change", renderGrade);
  }
}

function timetable(classId) {
  return entityTimetable("class", classId);
}

function entityTimetable(type, entityId) {
  const entity = {
    class: state.classes.find((item) => item.id === entityId),
    teacher: state.teachers.find((item) => item.id === entityId),
    room: state.rooms.find((item) => item.id === entityId),
  }[type];
  if (!entity) return `<p class="muted">Nada para exibir.</p>`;
  const lessons = state.lessons.filter((item) => {
    if (type === "teacher") return item.teacherId === entityId;
    if (type === "room") return item.roomId === entityId;
    return item.classId === entityId;
  });
  const days = type === "class" ? entity.days || schoolDays() : schoolDays();
  const periods = type === "class" ? periodsForClass(entity) : activePeriods();
  return `
    <div class="table-wrap">
      <table class="timetable">
        <thead><tr><th>Periodo</th>${days.map((day) => `<th>${day}</th>`).join("")}</tr></thead>
        <tbody>
          ${periods.map(
            (period) => `<tr>
              <th>${period}</th>
              ${days
                .map((day) => {
                  const lesson = lessons.find((item) => item.day === day && item.period === period);
                  const emptySlot = type === "class" ? `<button data-slot="${entityId}:${day}:${period}">Livre</button>` : `<span class="muted">Livre</span>`;
                  return `<td>${lesson ? lessonCard(lesson, type) : emptySlot}</td>`;
                })
                .join("")}
            </tr>`
          ).join("")}
        </tbody>
      </table>
    </div>`;
}

function generalTimetable() {
  return `
    <div class="table-wrap">
      <table class="timetable">
        <thead><tr><th>Periodo</th>${schoolDays().map((day) => `<th>${day}</th>`).join("")}</tr></thead>
        <tbody>
          ${activePeriods().map(
            (period) => `<tr>
              <th>${period}</th>
              ${schoolDays().map((day) => {
                const lessons = state.lessons.filter((item) => item.day === day && item.period === period);
                return `<td>${lessons.length ? lessons.map((lesson) => lessonCard(lesson, "general")).join("") : `<span class="muted">Sem aulas</span>`}</td>`;
              }).join("")}
            </tr>`
          ).join("")}
        </tbody>
      </table>
    </div>`;
}

function lessonCard(lesson, context = "class") {
  const lines = {
    class: [nameOf("teachers", lesson.teacherId), nameOf("rooms", lesson.roomId)],
    teacher: [nameOf("classes", lesson.classId), nameOf("rooms", lesson.roomId)],
    room: [nameOf("classes", lesson.classId), nameOf("teachers", lesson.teacherId)],
    general: [nameOf("classes", lesson.classId), nameOf("teachers", lesson.teacherId), nameOf("rooms", lesson.roomId)],
  }[context];
  const conflicts = conflictsForLesson(lesson.id);
  return `
    <div class="lesson ${conflicts.length ? "conflicted" : ""}">
      <strong>${nameOf("subjects", lesson.subjectId)}</strong>
      ${lines.map((line, index) => `<span class="${index > 0 ? "muted" : ""}">${line}</span>`).join("")}
      ${conflicts.length ? `<span class="conflict-label">${conflicts.length} conflito(s)</span>` : ""}
      <div class="actions no-print"><button data-edit-lesson="${lesson.id}">Editar</button><button data-remove-lesson="${lesson.id}">Remover</button></div>
    </div>`;
}

function renderRelatorios() {
  $("#relatorios").innerHTML = `
    <div class="report">
      <h2>${state.school.name}</h2>
      <p class="muted">Ano letivo ${state.school.year} | Pontuacao ${validation.score}</p>
      ${validation.quality ? `<p class="muted">Gerador: tentativa ${validation.quality.attempt}/${validation.quality.maxAttempts}, ${validation.quality.fixedLessons} aulas fixadas, ${validation.quality.teacherWindows} janelas.</p>` : ""}
      <h3>Conflitos</h3>
      <div class="list">${alertList(validation.conflicts, "danger")}</div>
      <h3>Cargas horarias pendentes</h3>
      <div class="list">${alertList(validation.pendencies)}</div>
      <h3>Grades por turma</h3>
      ${state.classes.map((schoolClass) => `<h4>${schoolClass.name}</h4>${timetable(schoolClass.id)}`).join("")}
      <h3>Grades por professor</h3>
      ${state.teachers.map((teacher) => `<h4>${teacher.name}</h4>${entityTimetable("teacher", teacher.id)}`).join("")}
      <h3>Grades por sala</h3>
      ${state.rooms.map((room) => `<h4>${room.name}</h4>${entityTimetable("room", room.id)}`).join("")}
      <h3>Exportacao</h3>
      <p><a href="/api/export">Baixar relatorio em TXT</a></p>
    </div>`;
}

function openModal(title, fields, onSubmit) {
  const template = $("#modalTemplate").content.cloneNode(true);
  const backdrop = $(".modal-backdrop", template);
  $("h3", template).textContent = title;
  $(".modal-body", template).innerHTML = `<div class="form-grid">${fields.join("")}</div>`;
  $(".close", template).addEventListener("click", () => backdrop.remove());
  $(".modal", template).addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    await onSubmit(data);
    backdrop.remove();
    render();
  });
  document.body.appendChild(template);
}

function input(name, label, value = "", type = "text") {
  return `<label>${label}<input name="${name}" type="${type}" value="${escapeHtml(value ?? "")}"></label>`;
}

function textarea(name, label, value = "") {
  return `<label class="span-2">${label}<textarea name="${name}">${escapeHtml(value ?? "")}</textarea></label>`;
}

function select(name, label, options, value = "") {
  return `<label>${label}<select name="${name}">${options
    .map((option) => `<option value="${option.value}" ${option.value === value ? "selected" : ""}>${option.label}</option>`)
    .join("")}</select></label>`;
}

function checkbox(name, label, checked = false) {
  return `<label>${label}<select name="${name}"><option value="false">Nao</option><option value="true" ${checked ? "selected" : ""}>Sim</option></select></label>`;
}

function escapeHtml(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function editCollection(key, item = null) {
  const current = item || {};
  const fields = {
    teachers: [
      input("name", "Nome", current.name),
      input("contact", "Telefone ou e-mail", current.contact),
      textarea("subjectsCsv", "Disciplinas que pode lecionar (IDs ou nomes separados por virgula)", listToCsv((current.subjects || []).map((subjectId) => nameOf("subjects", subjectId, subjectId)))),
      input("maxPerDay", "Limite de aulas por dia", current.maxPerDay || 5, "number"),
      input("maxSequential", "Limite de aulas seguidas", current.maxSequential || 4, "number"),
      textarea("preferences", "Preferencias de horario", current.preferences || ""),
    ],
    classes: [
      input("name", "Nome da turma", current.name),
      input("grade", "Serie/Ano", current.grade),
      select("shift", "Turno", shiftOptions(), current.shift || "manha"),
      input("students", "Quantidade de alunos", current.students || 0, "number"),
      select("defaultRoomId", "Sala padrao", [{ value: "", label: "Nenhuma" }, ...optionList(state.rooms)], current.defaultRoomId),
      textarea("daysCsv", "Dias de aula da turma", listToCsv(current.days || schoolDays())),
    ],
    subjects: [
      input("name", "Nome da disciplina", current.name),
      input("weeklyLoad", "Carga semanal padrao", current.weeklyLoad || 1, "number"),
      checkbox("allowDouble", "Permite aula dupla", current.allowDouble),
      checkbox("requireDouble", "Exige aula dupla", current.requireDouble),
      checkbox("avoidLast", "Evitar ultimo horario", current.avoidLast),
      input("requiredRoomType", "Tipo de sala exigido", current.requiredRoomType),
      textarea("notes", "Observacoes/restricoes da disciplina", current.notes || ""),
    ],
    rooms: [
      input("name", "Nome da sala/ambiente", current.name),
      input("capacity", "Capacidade", current.capacity || 30, "number"),
      input("type", "Tipo", current.type || "Sala comum"),
      textarea("compatibleSubjectsCsv", "Disciplinas compativeis (IDs ou nomes separados por virgula; vazio aceita todas)", listToCsv((current.compatibleSubjects || []).map((subjectId) => nameOf("subjects", subjectId, subjectId)))),
    ],
  }[key];
  openModal(item ? "Editar cadastro" : "Novo cadastro", fields, async (data) => {
    const next = { ...current, ...data, id: current.id || id() };
    if (key === "teachers") {
      next.subjects = resolveSubjectList(data.subjectsCsv);
      next.maxPerDay = Number(next.maxPerDay || 0);
      next.maxSequential = Number(next.maxSequential || 0);
      next.availability = normalizeAvailability(next.availability || defaultAvailability());
      delete next.subjectsCsv;
    }
    if (key === "classes") {
      next.shift = next.shift || "manha";
      next.days = csvToList(data.daysCsv).length ? csvToList(data.daysCsv) : schoolDays();
      next.students = Number(next.students || 0);
      delete next.daysCsv;
    }
    if (key === "subjects") {
      next.weeklyLoad = Number(next.weeklyLoad || 0);
      next.allowDouble = next.allowDouble === "true";
      next.requireDouble = next.requireDouble === "true";
      next.avoidLast = next.avoidLast === "true";
    }
    if (key === "rooms") {
      next.capacity = Number(next.capacity || 0);
      next.availability = next.availability || defaultRoomAvailability();
      next.compatibleSubjects = resolveSubjectList(data.compatibleSubjectsCsv);
      delete next.compatibleSubjectsCsv;
    }
    state[key] = [...state[key].filter((entry) => entry.id !== next.id), next];
    await save();
  });
}

function editSchool() {
  openModal(
    "Cadastro da escola",
    [
      input("name", "Nome da escola", state.school.name),
      input("address", "Endereco", state.school.address),
      input("year", "Ano letivo", state.school.year),
      textarea("daysCsv", "Dias letivos da semana", listToCsv(state.school.days || DAYS)),
      textarea("periodTimesText", "Horarios dos periodos: periodo; inicio; fim", periodTimesToText()),
    ],
    async (data) => {
      state.school = { ...state.school, ...data, days: csvToList(data.daysCsv).length ? csvToList(data.daysCsv) : DAYS };
      state.school.periodTimes = parsePeriodTimes(data.periodTimesText);
      delete state.school.daysCsv;
      delete state.school.periodTimesText;
      normalizeAllAvailability();
      await save();
    }
  );
}

function editShifts() {
  const value = (state.school.shifts || [])
    .map((shift) => `${shift.id}; ${shift.name}; ${(shift.periods || []).join(", ")}`)
    .join("\n");
  openModal(
    "Turnos e periodos",
    [
      textarea(
        "shiftsText",
        "Um turno por linha: id; nome; periodos separados por virgula",
        value || "manha; Manha; 1a aula, 2a aula, 3a aula, 4a aula, 5a aula"
      ),
    ],
    async (data) => {
      const shifts = parseShifts(data.shiftsText);
      if (!shifts.length) {
        alert("Informe ao menos um turno valido.");
        return;
      }
      state.school.shifts = shifts;
      normalizeAllAvailability();
      await save();
    }
  );
}

function editCurriculum(row = null) {
  const current = row || {};
  openModal(
    row ? "Editar matriz curricular" : "Novo vinculo curricular",
    [
      select("classId", "Turma", optionList(state.classes), current.classId),
      select("subjectId", "Disciplina", optionList(state.subjects), current.subjectId),
      select("teacherId", "Professor", optionList(state.teachers), current.teacherId),
      input("weeklyLessons", "Aulas semanais", current.weeklyLessons || 1, "number"),
      checkbox("requiresDouble", "Precisa de aula dupla", current.requiresDouble),
      select("specialRoomId", "Sala especial", [{ value: "", label: "Nenhuma" }, ...optionList(state.rooms)], current.specialRoomId),
      input("notes", "Restricoes especificas", current.notes),
    ],
    async (data) => {
      const next = {
        ...current,
        ...data,
        id: current.id || id(),
        weeklyLessons: Number(data.weeklyLessons || 0),
        requiresDouble: data.requiresDouble === "true",
      };
      state.curriculum = [...state.curriculum.filter((entry) => entry.id !== next.id), next];
      await save();
    }
  );
}

function editLesson(lesson = {}) {
  openModal(
    lesson.id ? "Editar aula" : "Inserir aula",
    [
      select("classId", "Turma", optionList(state.classes), lesson.classId),
      select("subjectId", "Disciplina", optionList(state.subjects), lesson.subjectId),
      select("teacherId", "Professor", optionList(state.teachers), lesson.teacherId),
      select("roomId", "Sala", optionList(state.rooms), lesson.roomId),
      select("day", "Dia", DAYS.map((day) => ({ value: day, label: day })), lesson.day),
      select("period", "Periodo", activePeriods().map((period) => ({ value: period, label: period })), lesson.period),
    ],
    async (data) => {
      const row = state.curriculum.find(
        (entry) => entry.classId === data.classId && entry.subjectId === data.subjectId && entry.teacherId === data.teacherId
      );
      const payload = { ...lesson, ...data, id: lesson.id || id(), curriculumId: lesson.curriculumId || row?.id || "", fixed: true };
      const response = await api("/api/lesson", { method: "POST", body: JSON.stringify(payload) });
      state = response.data;
      validation = response.validation;
      if (response.conflicts?.length) alert(`Conflitos encontrados:\n${response.conflicts.join("\n")}`);
    }
  );
}

function optionList(items) {
  return items.map((item) => ({ value: item.id, label: item.name }));
}

function shiftOptions() {
  return (state.school.shifts || []).map((shift) => ({ value: shift.id, label: shift.name }));
}

function resolveSubjectList(value) {
  const entries = csvToList(value);
  return entries
    .map((entry) => {
      const found = state.subjects.find((subject) => subject.id === entry || subject.name.toLowerCase() === entry.toLowerCase());
      return found?.id || entry;
    })
    .filter(Boolean);
}

function parseShifts(value) {
  return String(value || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [rawId, rawName, rawPeriods] = line.split(";").map((part) => part.trim());
      const periods = csvToList(rawPeriods);
      return rawId && rawName && periods.length ? { id: rawId, name: rawName, periods } : null;
    })
    .filter(Boolean);
}

function periodTimesToText() {
  const periodTimes = state.school.periodTimes || {};
  return activePeriods()
    .map((period) => {
      const time = periodTimes[period] || {};
      return `${period}; ${time.start || ""}; ${time.end || ""}`;
    })
    .join("\n");
}

function parsePeriodTimes(value) {
  const result = {};
  String(value || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const [period, start, end] = line.split(";").map((part) => part.trim());
      if (period) result[period] = { start: start || "", end: end || "" };
    });
  return result;
}

function defaultAvailability() {
  return Object.fromEntries(schoolDays().map((day) => [day, Object.fromEntries(activePeriods().map((period) => [period, "available"]))]));
}

function defaultRoomAvailability() {
  return Object.fromEntries(schoolDays().map((day) => [day, Object.fromEntries(activePeriods().map((period) => [period, true]))]));
}

function normalizeAvailability(existing) {
  return Object.fromEntries(
    schoolDays().map((day) => [
      day,
      Object.fromEntries(activePeriods().map((period) => [period, existing?.[day]?.[period] || "available"])),
    ])
  );
}

function normalizeRoomAvailability(existing) {
  return Object.fromEntries(
    schoolDays().map((day) => [
      day,
      Object.fromEntries(activePeriods().map((period) => [period, existing?.[day]?.[period] ?? true])),
    ])
  );
}

function normalizeAllAvailability() {
  state.teachers.forEach((teacher) => {
    teacher.availability = normalizeAvailability(teacher.availability);
  });
  state.rooms.forEach((room) => {
    room.availability = normalizeRoomAvailability(room.availability);
  });
  state.classes.forEach((schoolClass) => {
    schoolClass.days = (schoolClass.days || schoolDays()).filter((day) => schoolDays().includes(day));
    if (!schoolClass.days.length) schoolClass.days = schoolDays();
  });
}

function usageFor(key, itemId) {
  const labels = [];
  if (key === "teachers" && state.curriculum.some((row) => row.teacherId === itemId)) labels.push("matriz curricular");
  if (key === "teachers" && state.lessons.some((lesson) => lesson.teacherId === itemId)) labels.push("grade gerada");
  if (key === "classes" && state.curriculum.some((row) => row.classId === itemId)) labels.push("matriz curricular");
  if (key === "classes" && state.lessons.some((lesson) => lesson.classId === itemId)) labels.push("grade gerada");
  if (key === "subjects" && state.curriculum.some((row) => row.subjectId === itemId)) labels.push("matriz curricular");
  if (key === "subjects" && state.lessons.some((lesson) => lesson.subjectId === itemId)) labels.push("grade gerada");
  if (key === "rooms" && state.classes.some((schoolClass) => schoolClass.defaultRoomId === itemId)) labels.push("turma");
  if (key === "rooms" && state.curriculum.some((row) => row.specialRoomId === itemId)) labels.push("matriz curricular");
  if (key === "rooms" && state.lessons.some((lesson) => lesson.roomId === itemId)) labels.push("grade gerada");
  return [...new Set(labels)];
}

document.addEventListener("click", async (event) => {
  const target = event.target.closest("button");
  if (!target) return;
  if (target.dataset.view) {
    currentView = target.dataset.view;
    $$(".view").forEach((view) => view.classList.toggle("active", view.id === currentView));
    $$("nav button").forEach((button) => button.classList.toggle("active", button.dataset.view === currentView));
  }
  if (target.dataset.gradeMode) {
    gradeMode = target.dataset.gradeMode;
    renderGrade();
  }
  if (target.dataset.add) editCollection(target.dataset.add);
  if (target.dataset.edit) {
    const [key, itemId] = target.dataset.edit.split(":");
    editCollection(key, state[key].find((item) => item.id === itemId));
  }
  if (target.dataset.delete) {
    const [key, itemId] = target.dataset.delete.split(":");
    const usage = usageFor(key, itemId);
    if (usage.length) {
      alert(`Nao e possivel remover: este cadastro esta em uso em ${usage.join(", ")}.`);
      return;
    }
    if (!confirm("Remover este cadastro?")) return;
    state[key] = state[key].filter((item) => item.id !== itemId);
    await save();
  }
  if (target.dataset.editSchool !== undefined) editSchool();
  if (target.dataset.editShifts !== undefined) editShifts();
  if (target.dataset.addCurriculum !== undefined) editCurriculum();
  if (target.dataset.editCurriculum) editCurriculum(state.curriculum.find((item) => item.id === target.dataset.editCurriculum));
  if (target.dataset.avail) {
    const [teacherId, day, period] = target.dataset.avail.split(":");
    const teacher = state.teachers.find((item) => item.id === teacherId);
    teacher.availability[day][period] = teacher.availability[day][period] === "blocked" ? "available" : "blocked";
    await save();
  }
  if (target.dataset.addLesson !== undefined) editLesson();
  if (target.dataset.slot) {
    const [classId, day, period] = target.dataset.slot.split(":");
    editLesson({ classId, day, period });
  }
  if (target.dataset.editLesson) editLesson(state.lessons.find((item) => item.id === target.dataset.editLesson));
  if (target.dataset.removeLesson) {
    const payload = await api(`/api/lesson?id=${target.dataset.removeLesson}`, { method: "DELETE" });
    state = payload.data;
    validation = payload.validation;
    render();
  }
});

$("#saveBtn").addEventListener("click", save);
$("#generateBtn").addEventListener("click", generate);
$("#resetBtn").addEventListener("click", resetExample);
$("#printBtn").addEventListener("click", () => {
  currentView = "relatorios";
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === currentView));
  window.print();
});

load().catch((error) => {
  document.body.innerHTML = `<main class="view active"><div class="panel"><h1>Erro ao carregar</h1><pre>${error.message}</pre></div></main>`;
});
