document.addEventListener("DOMContentLoaded", () => {

  const especialidadeSelect = document.getElementById("especialidadeSelect");
  const medicoSelect = document.getElementById("id_medico");
  const dataInput = document.getElementById("data-futura");
  const grade = document.getElementById("grade-horarios");
  const resumoBox = document.getElementById("resumo-consulta");
  const resumoMedico = document.getElementById("resumo-medico");
  const resumoEsp = document.getElementById("resumo-especialidade");
  const resumoData = document.getElementById("resumo-data");
  const resumoHora = document.getElementById("resumo-hora");
  const resumoConvenioLine = document.getElementById("resumo-convenio-line");
  const resumoConvenio = document.getElementById("resumo-convenio");
  const btnConfirmar = document.getElementById("btnConfirmar");
  const inputHora = document.getElementById("id_hora");
  const inputDataHora = document.getElementById("id_data_hora");
  const modal = new bootstrap.Modal(document.getElementById("modalSucesso"));
  const progressBar = document.getElementById("progressBar");
  const modalResumo = document.getElementById("modalResumo");
  const mensagemErro = document.getElementById("mensagem-erro");
  const card = document.getElementById("cardConsulta");

  const usaConvenioCheckbox = document.getElementById("usa_convenio");
  const wrapperConvenio = document.getElementById("wrapper_convenio");
  const selectConvenio = document.getElementById("select_convenio");

  const hoje = new Date().toISOString().split("T")[0];
  dataInput.min = hoje;

  medicoSelect.disabled = true;
  btnConfirmar.disabled = true;

  usaConvenioCheckbox.addEventListener("change", () => {
    if (usaConvenioCheckbox.checked) {
      wrapperConvenio.style.display = "block";
      selectConvenio.required = true;
    } else {
      wrapperConvenio.style.display = "none";
      selectConvenio.required = false;
      selectConvenio.value = "";
      resumoConvenioLine.style.display = "none";
    }
    limparErrosCampos();
  });

  [especialidadeSelect, medicoSelect, dataInput, selectConvenio].forEach(el => {
    el.addEventListener('change', limparErrosCampos);
  });

  especialidadeSelect.addEventListener("change", () => {

    limparErrosCampos();

    const espId = especialidadeSelect.value;

    medicoSelect.innerHTML = '<option value="">Carregando médicos...</option>';
    medicoSelect.disabled = true;

    dataInput.readOnly = true;
    dataInput.classList.add("blocked-date");

    btnConfirmar.disabled = true;
    resumoBox.style.display = "none";
    grade.innerHTML = '<span class="text-muted small">Selecione o médico e o dia.</span>';

    if (!espId) return;

    fetch(`/consultas/medicos_por_especialidade/?especialidade_id=${espId}`)
      .then(r => r.json())
      .then(res => {

        medicoSelect.innerHTML = '<option value="">Selecione um médico</option>';

        if (res.medicos.length === 0) {
          medicoSelect.innerHTML = '<option value="">Nenhum médico encontrado</option>';
          return;
        }

        res.medicos.forEach(m => {
          const opt = document.createElement("option");
          opt.value = m.id;
          opt.textContent = `${m.nome} — ${m.especialidade}`;
          medicoSelect.appendChild(opt);
        });

        medicoSelect.disabled = false;
      });

  });

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
    resumoBox.style.display = "none";
  });

  dataInput.addEventListener("change", () => {

    limparErrosCampos();

    const data = dataInput.value;
    const medico = medicoSelect.value;

    if (!data || !medico) return;

    grade.innerHTML = '<span class="text-muted small">Carregando horários...</span>';

    fetch(`/consultas/horarios_disponiveis/?medico_id=${medico}&data=${data}`)
      .then(r => r.json())
      .then(res => {

        grade.innerHTML = '';

        const horarios = [
          "08:00","08:30","09:00","09:30",
          "10:00","10:30","11:00","11:30",
          "12:00","12:30","13:00","13:30",
          "14:00","14:30","15:00","15:30",
          "16:00","16:30"
        ];

        horarios.forEach(hora => {

          const btn = document.createElement("button");
          btn.type = "button";
          btn.textContent = hora;
          btn.className = "btn btn-horario";

          if (!res.horarios.includes(hora)) {
            btn.disabled = true;
            btn.title = "Horário indisponível";
          }

          btn.addEventListener("click", () => {
            document.querySelectorAll(".btn-horario").forEach(b => b.classList.remove("active"));

            btn.classList.add("active");

            inputHora.value = hora;
            inputDataHora.value = `${data} ${hora}`;

            btnConfirmar.disabled = false;

            resumoMedico.textContent = medicoSelect.options[medicoSelect.selectedIndex].text;
            resumoEsp.textContent = especialidadeSelect.options[especialidadeSelect.selectedIndex].text;
            resumoData.textContent = new Date(data).toLocaleDateString('pt-BR');
            resumoHora.textContent = hora;

            if (usaConvenioCheckbox.checked && selectConvenio.value) {
              resumoConvenio.textContent = selectConvenio.options[selectConvenio.selectedIndex].text;
              resumoConvenioLine.style.display = "list-item";
            } else {
              resumoConvenioLine.style.display = "none";
            }

            resumoBox.style.display = "block";
          });

          grade.appendChild(btn);

        });

      });

  });

  const form = document.getElementById("consultaForm");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    limparErrosCampos();

    const btnSpinner = document.getElementById("btn-spinner");
    const btnTexto = document.getElementById("btn-texto");
    btnSpinner.classList.remove("d-none");
    btnTexto.innerHTML = "Agendando...";

    const formData = new FormData(form);

    try {
      const res = await fetch("", {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" }
      });

      const data = await res.json();

      btnSpinner.classList.add("d-none");
      btnTexto.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Confirmar Consulta';

      if (data.ok) {

        modalResumo.innerHTML = `
          <strong>${data.consulta.medico}</strong><br>
          ${data.consulta.data} às ${data.consulta.hora}<br>
          Paciente: ${data.consulta.paciente}
          ${data.consulta.convenio ? `<br>Convênio: ${data.consulta.convenio}` : ''}
        `;

        modal.show();

        let p = 0;
        const timer = setInterval(() => {
          p += 4;
          progressBar.style.width = p + "%";
          if (p >= 100) {
            clearInterval(timer);
            window.location.href = "{% url 'listar_consultas' %}";
          }
        }, 90);

      } else {
        exibirErros(data.errors);
      }

    } catch (error) {
      exibirErroServidor();
      console.error(error);
    }

  });

});



/* EXIBE ERROS */

function exibirErros(errors) {

  const mensagemErro = document.getElementById("mensagem-erro");
  const card = document.getElementById("cardConsulta");

  let html = "";

  Object.keys(errors).forEach(campo => {
    const mensagens = errors[campo];

    const input = document.querySelector(`[name="${campo}"]`);
    if (input) input.classList.add("is-invalid");

    mensagens.forEach(msg => {
      html += `
        <div class="d-flex mb-1">
          <i class="bi bi-exclamation-octagon-fill text-danger me-2"></i>
          <span><strong>${formatarCampo(campo)}:</strong> ${msg}</span>
        </div>
      `;
    });
  });

  mensagemErro.innerHTML = html;
  mensagemErro.classList.remove("d-none");

  card.classList.add("shake");
  setTimeout(() => card.classList.remove("shake"), 500);
}


function limparErrosCampos() {
  document.getElementById("mensagem-erro").classList.add("d-none");
  document.getElementById("mensagem-erro").innerHTML = "";
  document.querySelectorAll(".is-invalid").forEach(el => el.classList.remove("is-invalid"));
}

function exibirErroServidor() {
  const msg = document.getElementById("mensagem-erro");
  msg.innerHTML = `
    <div class="d-flex">
      <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
      <span>Erro ao conectar com o servidor.</span>
    </div>
  `;
  msg.classList.remove("d-none");

  const card = document.getElementById("cardConsulta");
  card.classList.add("shake");
  setTimeout(() => card.classList.remove("shake"), 500);
}

function formatarCampo(campo) {
  const mapa = {
    medico: "Médico",
    data: "Data",
    hora: "Horário",
    observacoes: "Observações",
    convenio: "Convênio",
    usa_convenio: "Convênio",
    data_hora: "Data e Horário",
    __all__: "Erro"
  };
  return mapa[campo] || campo;
}
