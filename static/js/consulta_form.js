document.addEventListener("DOMContentLoaded", async () => {

  const especialidadeSelect = document.getElementById("especialidadeSelect");
  const medicoSelect = document.getElementById("id_medico");
  const dataInput = document.getElementById("data-futura");
  const grade = document.getElementById("grade-horarios");
  const btnConfirmar = document.getElementById("btnConfirmar");

  const usaConvenioCheckbox = document.getElementById("usa_convenio");
  const wrapperConvenio = document.getElementById("wrapper_convenio");
  const selectConvenio = document.getElementById("select_convenio");

  const inputHora = document.getElementById("id_hora");
  const inputDataHora = document.getElementById("id_data_hora");

  const mensagemErro = document.getElementById("mensagem-erro");

  // MODAL
  const modalEl = document.getElementById("modalResumo");
  const modal = new bootstrap.Modal(modalEl);
  let redirectUrl = "/consultas/";

  // Campos resumo
  const rPaciente = document.getElementById("resPaciente");
  const rMedico = document.getElementById("resMedico");
  const rEspecialidade = document.getElementById("resEspecialidade");
  const rData = document.getElementById("resData");
  const rHora = document.getElementById("resHora");
  const rConvenio = document.getElementById("resConvenio");

  // BOTÃO OK DO MODAL
  document.getElementById("btnModalOk").addEventListener("click", () => {
    window.location.href = redirectUrl;
  });

  // ========================================================
  // CAMPOS DO MODO EDIÇÃO
  // ========================================================
  const isEdicao = document.getElementById("isEdicao").value === "1";

  const edEspecialidade = document.getElementById("consultaEspecialidade").value;
  const edMedico = document.getElementById("consultaMedico").value;
  const edData = document.getElementById("consultaData").value;
  const edHora = document.getElementById("consultaHora").value;
  const edConvenio = document.getElementById("consultaConvenio").value;
  const edUsaConvenio = document.getElementById("consultaUsaConvenio").value === "1";

  // ========================================================
  // CONFIGURAÇÕES PADRÃO
  // ========================================================
  const hoje = new Date().toISOString().split("T")[0];
  dataInput.min = hoje;

  medicoSelect.disabled = true;
  btnConfirmar.disabled = true;

  // ========================================================
  // MODO EDIÇÃO — CARREGAMENTO AUTOMÁTICO
  // ========================================================
  if (isEdicao) {

    if (edEspecialidade) especialidadeSelect.value = edEspecialidade;

    await fetch(`/consultas/medicos_por_especialidade/?especialidade_id=${edEspecialidade}`)
      .then(r => r.json())
      .then(res => {
        medicoSelect.innerHTML = '<option value="">Selecione</option>';

        res.medicos.forEach(m => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = `${m.nome} — ${m.especialidade}`;
          medicoSelect.appendChild(opt);
        });

        medicoSelect.disabled = false;

        setTimeout(() => {
          medicoSelect.value = edMedico;
        }, 100);
      });

    dataInput.readOnly = false;
    dataInput.classList.remove("blocked-date");
    dataInput.value = edData;

    if (edUsaConvenio) {
      usaConvenioCheckbox.checked = true;
      wrapperConvenio.style.display = "block";

      setTimeout(() => {
        selectConvenio.value = edConvenio;
      }, 150);
    }

    await fetch(`/consultas/horarios_disponiveis/?medico_id=${edMedico}&data=${edData}`)
      .then(r => r.json())
      .then(res => {

        grade.innerHTML = "";

        const horarios = [
          "08:00","08:30","09:00","09:30",
          "10:00","10:30","11:00","11:30",
          "12:00","12:30","13:00","13:30",
          "14:00","14:30","15:00","15:30",
          "16:00","16:30"
        ];

        horarios.forEach(h => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.textContent = h;
          btn.className = "btn btn-horario";

          if (!res.horarios.includes(h) && h !== edHora) btn.disabled = true;

          if (h === edHora) {
            btn.classList.add("active");
            inputHora.value = edHora;
            inputDataHora.value = `${edData} ${edHora}`;
            btnConfirmar.disabled = false;
          }

          btn.addEventListener("click", () => {
            document.querySelectorAll(".btn-horario").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            inputHora.value = h;
            inputDataHora.value = `${edData} ${h}`;
            btnConfirmar.disabled = false;
          });

          grade.appendChild(btn);
        });

      });

  }

  // ========================================================
  // NOVA CONSULTA — TROCA DE ESPECIALIDADE
  // ========================================================
  especialidadeSelect.addEventListener("change", () => {

    limparErrosCampos();

    const especialidadeId = especialidadeSelect.value;

    medicoSelect.innerHTML = '<option value="">Carregando médicos...</option>';
    medicoSelect.disabled = true;

    dataInput.readOnly = true;
    dataInput.classList.add("blocked-date");

    btnConfirmar.disabled = true;

    grade.innerHTML = '<span class="text-muted small">Selecione o médico e o dia.</span>';

    if (!especialidadeId) return;

    fetch(`/consultas/medicos_por_especialidade/?especialidade_id=${especialidadeId}`)
      .then(r => r.json())
      .then(res => {
        medicoSelect.innerHTML = '<option value="">Selecione</option>';

        res.medicos.forEach(m => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = `${m.nome} — ${m.especialidade}`;
          medicoSelect.appendChild(opt);
        });

        medicoSelect.disabled = false;
      });
  });

  // ========================================================
  // MÉDICO → habilitar data
  // ========================================================
  medicoSelect.addEventListener("change", () => {
    limparErrosCampos();

    if (medicoSelect.value) {
      dataInput.readOnly = false;
      dataInput.classList.remove("blocked-date");
    } else {
      dataInput.readOnly = true;
      dataInput.classList.add("blocked-date");
    }

    grade.innerHTML = '<span class="text-muted small">Selecione uma data.</span>';
  });

  // ========================================================
  // DATA → carregar horários
  // ========================================================
  dataInput.addEventListener("change", () => {

    limparErrosCampos();

    const data = dataInput.value;
    const medico = medicoSelect.value;

    if (!data || !medico) return;

    grade.innerHTML = '<span class="text-muted small">Carregando horários...</span>';

    fetch(`/consultas/horarios_disponiveis/?medico_id=${medico}&data=${data}`)
      .then(r => r.json())
      .then(res => {

        grade.innerHTML = "";

        const horarios = [
          "08:00","08:30","09:00","09:30",
          "10:00","10:30","11:00","11:30",
          "12:00","12:30","13:00","13:30",
          "14:00","14:30","15:00","15:30",
          "16:00","16:30"
        ];

        horarios.forEach(h => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.textContent = h;
          btn.className = "btn btn-horario";

          if (!res.horarios.includes(h)) btn.disabled = true;

          btn.addEventListener("click", () => {
            document.querySelectorAll(".btn-horario").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            inputHora.value = h;
            inputDataHora.value = `${data} ${h}`;

            btnConfirmar.disabled = false;
          });

          grade.appendChild(btn);
        });

      });

  });

  // ========================================================
  // CONVÊNIO
  // ========================================================
  usaConvenioCheckbox.addEventListener("change", () => {
    if (usaConvenioCheckbox.checked) {
      wrapperConvenio.style.display = "block";
      selectConvenio.required = true;
    } else {
      wrapperConvenio.style.display = "none";
      selectConvenio.required = false;
      selectConvenio.value = "";
    }
  });

  // ========================================================
  // SUBMIT → AJAX + MODAL RESUMO
  // ========================================================
  const form = document.getElementById("consultaForm");

  form.addEventListener("submit", async e => {
    e.preventDefault();

    const formData = new FormData(form);

    try {
      const res = await fetch("", {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });

      const data = await res.json();

      if (!data.ok) {
        exibirErros(data.errors);
        return;
      }

      // ==============================
      // PREENCHER MODAL
      // ==============================
      redirectUrl = "/consultas/";

      rPaciente.textContent = data.consulta.paciente;
      rMedico.textContent = data.consulta.medico;
      rEspecialidade.textContent = data.consulta.especialidade || "";
      rData.textContent = data.consulta.data;
      rHora.textContent = data.consulta.hora;
      rConvenio.textContent = data.consulta.convenio || "Nenhum";

      modal.show();

    } catch (err) {
      console.error(err);
      exibirErroServidor();
    }

  });

  // ========================================================
  // FUNÇÕES AUXILIARES
  // ========================================================
  function limparErrosCampos() {
    mensagemErro.classList.add("d-none");
    mensagemErro.innerHTML = "";
    document.querySelectorAll(".is-invalid").forEach(el => el.classList.remove("is-invalid"));
  }

  function exibirErros(errors) {
    let html = "";

    Object.keys(errors).forEach(campo => {
      const mensagens = errors[campo];

      const input = document.querySelector(`[name="${campo}"]`);
      if (input) input.classList.add("is-invalid");

      mensagens.forEach(msg => {
        html += `
          <div class="d-flex mb-1">
            <i class="bi bi-exclamation-octagon-fill text-danger me-2"></i>
            <span><strong>${campo}:</strong> ${msg}</span>
          </div>`;
      });
    });

    mensagemErro.innerHTML = html;
    mensagemErro.classList.remove("d-none");
  }

  function exibirErroServidor() {
    mensagemErro.innerHTML = `
      <div class="d-flex">
        <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
        <span>Erro ao conectar com o servidor.</span>
      </div>
    `;

    mensagemErro.classList.remove("d-none");
  }

});
