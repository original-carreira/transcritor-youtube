// ==============================
// COPIAR TEXTO
// ==============================

function copiarTexto() {
    const textarea = document.querySelector('textarea[name="texto"]');
    
    if (!textarea) return;

    const texto = textarea.value;

    navigator.clipboard.writeText(texto).then(() => {
        const msg = document.getElementById('copiado-msg');
        
        if (msg) {
            msg.style.display = 'inline';

            setTimeout(() => {
                msg.style.display = 'none';
            }, 2000);
        }
    }).catch(err => {
        console.error('Erro ao copiar: ', err);
    });
}


// ==============================
// LOADING
// ==============================

function mostrarLoading() {
    const loading = document.getElementById('loading');
    const botao = document.getElementById('btn-submit');

    if (loading) {
        loading.style.display = 'inline';
    }

    if (botao) {
        botao.disabled = true;
    }
}

// ==============================
// LIMPAR URL
// ==============================

function limparURL() {
    const campo = document.getElementById("url");

    if (campo) {
        campo.value = "";
        campo.focus();
    }
}