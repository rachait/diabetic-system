// Multi-Step Form Logic
const steps = [
    {
        label: 'Age',
        desc: 'Enter your age in years.',
        icon: 'assets/age.svg',
        input: '<input type="number" min="1" max="120" name="age" class="input-field" required>'
    },
    {
        label: 'Gender',
        desc: 'Select your gender.',
        icon: 'assets/gender.svg',
        input: `<select name="gender" class="input-field" required><option value="">Select</option><option value="Male">Male</option><option value="Female">Female</option><option value="Other">Other</option></select>`
    },
    {
        label: 'Family History',
        desc: 'Any family history of diabetes?',
        icon: 'assets/family.svg',
        input: `<select name="family_history" class="input-field" required><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option></select>`
    },
    {
        label: 'Blood Pressure',
        desc: 'Do you have high blood pressure?',
        icon: 'assets/blood-pressure.svg',
        input: `<select name="blood_pressure" class="input-field" required><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option></select>`
    },
    {
        label: 'Activity',
        desc: 'How active are you?',
        icon: 'assets/activity.svg',
        input: `<select name="activity" class="input-field" required><option value="">Select</option><option value="Low">Low</option><option value="Moderate">Moderate</option><option value="High">High</option></select>`
    },
    {
        label: 'Race',
        desc: 'Select your race/ethnicity.',
        icon: 'assets/race.svg',
        input: `<select name="race" class="input-field" required><option value="">Select</option><option value="White">White</option><option value="Black">Black</option><option value="Asian">Asian</option><option value="Hispanic">Hispanic</option><option value="Other">Other</option></select>`
    },
    {
        label: 'BMI',
        desc: 'Enter your Body Mass Index.',
        icon: 'assets/bmi.svg',
        input: '<input type="number" min="10" max="60" step="0.1" name="bmi" class="input-field" required>'
    },
    {
        label: 'Prediabetes',
        desc: 'Have you been diagnosed with prediabetes?',
        icon: 'assets/prediabetes.svg',
        input: `<select name="prediabetes" class="input-field" required><option value="">Select</option><option value="Yes">Yes</option><option value="No">No</option></select>`
    },
    {
        label: 'Medical Parameters',
        desc: 'Enter your medical details.',
        icon: 'assets/medical.svg',
        input: `
        <div class="input-group"><label>Pregnancies</label><input type="number" min="0" max="20" name="pregnancies" class="input-field" required></div>
        <div class="input-group"><label>Glucose</label><input type="number" min="0" max="300" name="glucose" class="input-field" required></div>
        <div class="input-group"><label>Blood Pressure</label><input type="number" min="0" max="200" name="bp" class="input-field" required></div>
        <div class="input-group"><label>Skin Thickness</label><input type="number" min="0" max="100" name="skin" class="input-field" required></div>
        <div class="input-group"><label>Insulin</label><input type="number" min="0" max="900" name="insulin" class="input-field" required></div>
        <div class="input-group"><label>BMI</label><input type="number" min="10" max="60" step="0.1" name="bmi2" class="input-field" required></div>
        <div class="input-group"><label>DPF</label><input type="number" min="0.01" max="2.5" step="0.01" name="dpf" class="input-field" required></div>
        <div class="input-group"><label>Age</label><input type="number" min="1" max="120" name="age2" class="input-field" required></div>
        `
    }
];

// Login Modal Logic
document.addEventListener('DOMContentLoaded', function() {
    // Open modal from any Login link on the page
    const loginLinks = document.querySelectorAll('a[href="#login"]');
    const loginModal = document.getElementById('loginModal');
    const closeLoginModal = document.getElementById('closeLoginModal');
    const loginForm = document.getElementById('loginForm');
    const loginError = document.getElementById('loginError');

    if (loginLinks.length && loginModal) {
        loginLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                loginModal.style.display = 'flex';
            });
        });
    }
    if (closeLoginModal) {
        closeLoginModal.addEventListener('click', function() {
            loginModal.style.display = 'none';
            loginError.style.display = 'none';
        });
    }
    // Close modal on outside click
    window.addEventListener('click', function(e) {
        if (e.target === loginModal) {
            loginModal.style.display = 'none';
            loginError.style.display = 'none';
        }
    });
    // Handle login form submit
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loginError.style.display = 'none';
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            // TODO: Replace with real authentication API call
            if (email === 'admin@example.com' && password === 'password') {
                alert('Login successful!');
                loginModal.style.display = 'none';
            } else {
                loginError.textContent = 'Invalid email or password.';
                loginError.style.display = 'block';
            }
        });
    }
});

const form = document.getElementById('riskForm');
const progressBar = document.getElementById('progress-bar');
let currentStep = 0;
let formData = {};

function renderStep(stepIdx) {
    form.innerHTML = '';
    const step = steps[stepIdx];
    const stepDiv = document.createElement('div');
    stepDiv.className = 'form-step active';
    stepDiv.innerHTML = `
        <div class="input-group">
            <label class="input-label">${step.label}</label>
            <span class="input-desc">${step.desc}</span>
            <div style="position:relative;">
                <img src="${step.icon}" class="input-icon" alt="icon">
                ${step.input}
            </div>
        </div>
    `;
    form.appendChild(stepDiv);

    // Add buttons
    const btnsDiv = document.createElement('div');
    btnsDiv.className = 'form-btns';
    if (stepIdx > 0) {
        const backBtn = document.createElement('button');
        backBtn.type = 'button';
        backBtn.className = 'btn-clear';
        backBtn.textContent = 'Back';
        backBtn.onclick = () => {
            currentStep--;
            renderStep(currentStep);
        };
        btnsDiv.appendChild(backBtn);
    }
    if (stepIdx < steps.length - 1) {
        const nextBtn = document.createElement('button');
        nextBtn.type = 'button';
        nextBtn.className = 'btn-gradient';
        nextBtn.textContent = 'Next';
        nextBtn.onclick = () => {
            if (validateStep(stepIdx)) {
                saveStepData(stepIdx);
                currentStep++;
                renderStep(currentStep);
            }
        };
        btnsDiv.appendChild(nextBtn);
    } else {
        const predictBtn = document.createElement('button');
        predictBtn.type = 'submit';
        predictBtn.className = 'btn-gradient';
        predictBtn.textContent = 'Predict Risk';
        btnsDiv.appendChild(predictBtn);
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'btn-clear';
        clearBtn.textContent = 'Clear';
        clearBtn.onclick = () => {
            formData = {};
            currentStep = 0;
            renderStep(currentStep);
        };
        btnsDiv.appendChild(clearBtn);
    }
    form.appendChild(btnsDiv);
    updateProgressBar(stepIdx);
}

function updateProgressBar(idx) {
    const percent = ((idx + 1) / steps.length) * 100;
    progressBar.style.width = percent + '%';
}

function validateStep(idx) {
    const step = steps[idx];
    const input = form.querySelector('.input-field');
    if (!input) return false;
    if (!input.checkValidity()) {
        input.reportValidity();
        return false;
    }
    return true;
}

function saveStepData(idx) {
    const step = steps[idx];
    if (idx === steps.length - 1) {
        // Last step: collect all fields
        const fields = form.querySelectorAll('.input-field');
        fields.forEach(f => {
            formData[f.name] = f.value;
        });
    } else {
        const input = form.querySelector('.input-field');
        formData[input.name] = input.value;
    }
}

form.onsubmit = async function(e) {
    e.preventDefault();
    saveStepData(currentStep);
    // Prepare data for backend
    const payload = {
        pregnancies: Number(formData.pregnancies || formData.pregnancies || 0),
        glucose: Number(formData.glucose || 0),
        blood_pressure: Number(formData.bp || formData.blood_pressure || 0),
        skin_thickness: Number(formData.skin || 0),
        insulin: Number(formData.insulin || 0),
        bmi: Number(formData.bmi2 || formData.bmi || 0),
        diabetes_pedigree: Number(formData.dpf || 0),
        age: Number(formData.age2 || formData.age || 0)
    };
    showResult('Loading...', 'info');
    try {
        const response = await fetch('http://localhost:5000/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (data && data.status === 'success') {
            let level = 'low';
            if (data.prediction_value === 1) {
                if (data.confidence >= 0.8) level = 'high';
                else level = 'medium';
            }
            showResult(`${data.prediction} (Confidence: ${data.confidence ? (data.confidence*100).toFixed(1)+'%' : 'N/A'})`, level);
        } else {
            showResult('Prediction failed', 'error');
        }
    } catch (err) {
        showResult('Server error', 'error');
    }
};

function showResult(risk, level) {
    const resultSection = document.getElementById('result');
    const resultBox = document.getElementById('resultBox');
    let icon = 'assets/health-icon.svg';
    let cls = '';
    if (level === 'low') {
        icon = 'assets/success.svg';
        cls = 'result-low';
    } else if (level === 'medium') {
        icon = 'assets/warning.svg';
        cls = 'result-medium';
    } else if (level === 'high') {
        icon = 'assets/danger.svg';
        cls = 'result-high';
    }
    resultBox.innerHTML = `
        <img src="${icon}" class="result-icon" alt="Result Icon">
        <div class="${cls}">${risk}</div>
        <button class="btn-gradient" onclick="location.reload()">Try Again</button>
    `;
    resultSection.style.display = 'block';
    window.scrollTo({ top: resultSection.offsetTop - 40, behavior: 'smooth' });
}

// Initial render
renderStep(currentStep);
