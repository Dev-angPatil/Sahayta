// src/sahayta/static/app.js
// Interactive Frontend Controller for Project Sahayta
// Governed by Command Center DESIGN.md standards

let currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 10);
let currentDraft = null;
let isProcessing = false;

const portalUrlMapping = {
  'CPGRAMS': 'https://pgportal.gov.in/Grievance/NewFiling',
  'GOVTECH_CPGRAMS_V1': 'https://pgportal.gov.in/Grievance/NewFiling',
  'STATE_PDS': 'https://nfsa.gov.in/StatePDS/GrievancePortal',
  'GOVTECH_STATE_PDS_V1': 'https://nfsa.gov.in/StatePDS/GrievancePortal',
  'DISCOM_POWER': 'https://cgrf.gov.in/ConsumerRedressal/DocketEntry',
  'GOVTECH_UTILITY_DISCOM_V1': 'https://cgrf.gov.in/ConsumerRedressal/DocketEntry',
  'WATER_BOARD': 'https://delhijalboard.delhi.gov.in/PublicGrievance/QuickFiling',
  'GOVTECH_UTILITY_WATER_V1': 'https://delhijalboard.delhi.gov.in/PublicGrievance/QuickFiling',
};

document.addEventListener('DOMContentLoaded', () => {
  const sessionBadge = document.getElementById('session-badge');
  if (sessionBadge) sessionBadge.textContent = 'Session: Active';

  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const lodgeBtn = document.getElementById('btn-lodge-filing');
  const newSessionBtn = document.getElementById('new-session-btn');

  // Tab Switching
  const tabFormBtn = document.getElementById('tab-form-btn');
  const tabPetitionBtn = document.getElementById('tab-petition-btn');
  const portalFormView = document.getElementById('portal-form-view');
  const petitionView = document.getElementById('petition-view');

  if (tabFormBtn && tabPetitionBtn) {
    tabFormBtn.addEventListener('click', () => {
      tabFormBtn.classList.add('active');
      tabPetitionBtn.classList.remove('active');
      portalFormView.classList.remove('hidden');
      petitionView.classList.add('hidden');
    });

    tabPetitionBtn.addEventListener('click', () => {
      tabPetitionBtn.classList.add('active');
      tabFormBtn.classList.remove('active');
      petitionView.classList.remove('hidden');
      portalFormView.classList.add('hidden');
    });
  }

  // Automatic Language Detection (Hindi vs English)
  function detectTextLanguage(text) {
    if (!text || typeof text !== 'string') return 'hi';
    if (/[\u0900-\u097F]/.test(text)) return 'hi';
    const vernacularRegex = /\b(nahi|nahin|hai|hain|mera|meri|mere|khatam|ration|bijli|pani|paani|kaat|paisa|paise|shikayat|kripya|aadhaar|yojana|sarkar|babu|ghotala|bribe|docket|kachra|sadak|chori|bhook|mandi|dalal|hafta|bolta|bolti|karwa|bhejo|sunwai|darj|adhikari|sahayta|yahan|wahan|kaise|karo|raha|rahi|rahe|diya|de|liya|le|batao|madad|mujhe|humko|karo|bhai|saab)\b/i;
    if (vernacularRegex.test(text)) return 'hi';
    return 'en';
  }

  // Text-To-Speech (TTS) Engine
  let ttsEnabled = true;

  function speakText(text) {
    if (!ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();

    let cleanText = text
      .replace(/\[REJECTION:[^\]]+\]/g, '')
      .replace(/\*\*([^*]+)\*\*/g, '$1')
      .replace(/\*([^*]+)\*/g, '$1')
      .replace(/<[^>]*>/g, '')
      .replace(/[•#_`]/g, '')
      .trim();

    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.05;
    const isHindi = detectTextLanguage(cleanText) === 'hi';
    utterance.lang = isHindi ? 'hi-IN' : 'en-IN';

    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
      if (isHindi) {
        const hiVoice = voices.find(v => v.lang.startsWith('hi') || v.lang.includes('IN'));
        if (hiVoice) utterance.voice = hiVoice;
      } else {
        const enVoice = voices.find(v => v.lang === 'en-IN') || voices.find(v => v.lang.startsWith('en'));
        if (enVoice) utterance.voice = enVoice;
      }
    }
    window.speechSynthesis.speak(utterance);
  }

  const ttsToggleBtn = document.getElementById('tts-toggle-btn');
  if (ttsToggleBtn) {
    ttsToggleBtn.addEventListener('click', () => {
      ttsEnabled = !ttsEnabled;
      if (!ttsEnabled && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      ttsToggleBtn.classList.toggle('active', ttsEnabled);
      ttsToggleBtn.textContent = ttsEnabled ? '🔊 TTS' : '🔇 Muted';
      ttsToggleBtn.title = ttsEnabled ? 'Voice readout enabled' : 'Voice readout muted';
    });
  }

  // Voice Input via Web Speech API
  const voiceBtn = document.getElementById('voice-btn');
  const voiceLabel = document.getElementById('voice-label');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  let isVoiceListening = false;
  let accumulatedTranscript = '';
  let speechRecognitionInstance = null;

  function getEffectiveSpeechLang() {
    const text = userInput ? userInput.value : '';
    return detectTextLanguage(text) === 'hi' ? 'hi-IN' : 'en-IN';
  }

  function toggleVoiceRecognition() {
    if (!speechRecognitionInstance) return;
    if (isVoiceListening) {
      speechRecognitionInstance.stop();
    } else {
      accumulatedTranscript = '';
      speechRecognitionInstance.lang = getEffectiveSpeechLang();
      try {
        speechRecognitionInstance.start();
      } catch (err) {
        console.warn('Speech recognition start error:', err);
      }
    }
  }

  if (SpeechRecognition && voiceBtn) {
    speechRecognitionInstance = new SpeechRecognition();
    speechRecognitionInstance.continuous = false;
    speechRecognitionInstance.interimResults = true;
    speechRecognitionInstance.maxAlternatives = 1;

    voiceBtn.addEventListener('click', () => {
      toggleVoiceRecognition();
    });

    speechRecognitionInstance.onstart = () => {
      isVoiceListening = true;
      voiceBtn.classList.add('listening');
      if (voiceLabel) voiceLabel.textContent = 'Listening...';
      if (userInput) {
        userInput.placeholder = 'Listening... Speak now in Hindi, English, or Hinglish...';
      }
    };

    speechRecognitionInstance.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const piece = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          accumulatedTranscript += piece;
        } else {
          interim += piece;
        }
      }
      const combined = (accumulatedTranscript + ' ' + interim).trim();
      if (userInput && combined) {
        userInput.value = combined;
      }
    };

    speechRecognitionInstance.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      if (voiceLabel) {
        if (event.error === 'no-speech') {
          voiceLabel.textContent = 'No voice detected';
        } else if (event.error === 'not-allowed') {
          voiceLabel.textContent = 'Mic Blocked';
        }
      }
      cleanupVoice();
    };

    speechRecognitionInstance.onend = () => {
      cleanupVoice();
      if (userInput && userInput.value.trim().length > 3) {
        if (voiceLabel) voiceLabel.textContent = 'Transcribed ✓';
        setTimeout(() => {
          if (voiceLabel) voiceLabel.textContent = 'Voice';
          sendCitizenMessage();
        }, 500);
      }
    };

    function cleanupVoice() {
      isVoiceListening = false;
      voiceBtn.classList.remove('listening');
      if (userInput) {
        userInput.placeholder = 'Speak or type your complaint (Hindi, English, or Hinglish)...';
      }
      setTimeout(() => {
        if (voiceLabel && !isVoiceListening) voiceLabel.textContent = 'Voice';
      }, 1500);
    }
  } else if (voiceBtn) {
    voiceBtn.title = 'Speech recognition supported in Chrome/Edge/Safari';
    voiceBtn.addEventListener('click', () => {
      alert('Voice recognition works best on Chrome, Edge, Brave, or Safari browsers.');
    });
  }

  // Pressing Space should enable audio input
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' || e.key === ' ') {
      const active = document.activeElement;
      // If user is inside textarea and currently typing text, let normal space character insert!
      if (active === userInput && userInput.value.length > 0 && !isVoiceListening) {
        return;
      }
      e.preventDefault();
      toggleVoiceRecognition();
    }
  });

  // Handle enter key in textarea
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendCitizenMessage();
    }
  });

  // Handle form submit button
  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      sendCitizenMessage();
    });
  }

  // Handle direct petition submission confirmation
  if (lodgeBtn) {
    lodgeBtn.addEventListener('click', async () => {
      lodgeBtn.disabled = true;
      lodgeBtn.textContent = 'Lodging Grievance on Portal...';

      try {
        const response = await fetch('/api/v1/agent/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: currentSessionId,
            citizen_confirmation: true,
          }),
        });

        const data = await response.json();
        if (response.ok && data.receipt) {
          renderDocket(data.receipt);
          updateWorkflowStepper('SUBMITTED');
          appendMessage('agent', `Grievance successfully submitted! Official Reference: ${data.receipt.tracking_number}`);
          speakText(`Grievance successfully submitted. Official reference ${data.receipt.tracking_number}`);
          const actionBox = document.getElementById('submit-action-box');
          if (actionBox) actionBox.classList.add('hidden');
        } else {
          alert(data.detail || 'Filing execution failed.');
        }
      } catch (err) {
        alert(`Error executing filing: ${err.message}`);
      } finally {
        lodgeBtn.disabled = false;
        lodgeBtn.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
          <span>Confirm & Lodge Official Grievance</span>
        `;
      }
    });
  }

  function resetSession() {
    currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 10);
    currentDraft = null;
    if (sessionBadge) sessionBadge.textContent = 'Session: Active';

    // Reset messages (keep welcome)
    const container = document.getElementById('messages-container');
    const welcome = container.querySelector('.msg-system');
    container.innerHTML = '';
    if (welcome) container.appendChild(welcome);

    // Reset form fields
    resetFormSandbox();
    if (userInput) {
      userInput.value = '';
      userInput.focus();
    }
  }

  // New Session Button
  if (newSessionBtn) {
    newSessionBtn.addEventListener('click', () => {
      stopDemo();
      resetSession();
    });
  }

  // Automated Interactive Demo Mode
  let isDemoRunning = false;
  let demoTimeouts = [];

  function queueDemo(fn, delayMs) {
    const t = setTimeout(fn, delayMs);
    demoTimeouts.push(t);
    return t;
  }

  function stopDemo() {
    isDemoRunning = false;
    demoTimeouts.forEach(clearTimeout);
    demoTimeouts = [];

    const demoBtn = document.getElementById('demo-mode-btn');
    if (demoBtn) {
      demoBtn.classList.remove('active');
      demoBtn.textContent = '▶ Auto Demo';
    }

    const demoBanner = document.getElementById('demo-banner');
    if (demoBanner) demoBanner.classList.add('hidden');
  }

  function typeTextIntoInput(text, callback) {
    if (!isDemoRunning || !userInput) return;
    userInput.focus();
    userInput.value = '';
    let i = 0;
    const interval = setInterval(() => {
      if (!isDemoRunning) {
        clearInterval(interval);
        return;
      }
      userInput.value += text[i];
      i++;
      if (i >= text.length) {
        clearInterval(interval);
        setTimeout(callback, 280);
      }
    }, 22);
  }

  function startDemo() {
    if (isDemoRunning) {
      stopDemo();
      return;
    }

    isDemoRunning = true;
    const demoBtn = document.getElementById('demo-mode-btn');
    if (demoBtn) {
      demoBtn.classList.add('active');
      demoBtn.textContent = '⏸ Stop Demo';
    }

    const demoBanner = document.getElementById('demo-banner');
    const demoStepText = document.getElementById('demo-step-text');
    if (demoBanner) demoBanner.classList.remove('hidden');

    resetSession();

    // Turn 1: Initial grievance intake
    if (demoStepText) demoStepText.textContent = 'Demo Stage 1/5: Citizen Intake & Sovereign Routing (Railways / CPGRAMS)';

    queueDemo(() => {
      if (!isDemoRunning) return;
      typeTextIntoInput('IRCTC train 12952 ticket refund delayed for 16 days, PNR 2458971234. My name is Ramesh Sharma', () => {
        if (!isDemoRunning) return;
        sendCitizenMessage();

        // Turn 2: Elicitation (Mobile)
        queueDemo(() => {
          if (!isDemoRunning) return;
          if (demoStepText) demoStepText.textContent = 'Demo Stage 2/5: Evidentiary Elicitation (Mobile Verification)';
          typeTextIntoInput('7038932342', () => {
            if (!isDemoRunning) return;
            sendCitizenMessage();

            // Turn 3: Elicitation (Email)
            queueDemo(() => {
              if (!isDemoRunning) return;
              if (demoStepText) demoStepText.textContent = 'Demo Stage 3/5: Parameter Elicitation (Receipt Dispatch Address)';
              typeTextIntoInput('ramesh.sharma@gmail.com', () => {
                if (!isDemoRunning) return;
                sendCitizenMessage();

                // Turn 4: Article 350 Legal Petition Synthesis
                queueDemo(() => {
                  if (!isDemoRunning) return;
                  if (demoStepText) demoStepText.textContent = 'Demo Stage 4/5: Synthesizing Formal Article 350 Petition & Citizen Review Gate';

                  // Turn 5: Affirmative Consent & Official Filing
                  queueDemo(() => {
                    if (!isDemoRunning) return;
                    if (demoStepText) demoStepText.textContent = 'Demo Stage 5/5: Affirmative Consent & Cryptographic Docket Notarization';

                    const lodgeBtn = document.getElementById('btn-lodge-filing');
                    if (lodgeBtn) {
                      lodgeBtn.classList.add('missing-pulse');
                      setTimeout(() => {
                        lodgeBtn.classList.remove('missing-pulse');
                        lodgeBtn.click();
                      }, 1000);
                    }

                    queueDemo(() => {
                      if (!isDemoRunning) return;
                      if (demoStepText) demoStepText.textContent = '✓ Demo Complete: Official Docket Lodged with SHA-256 Tamper-Proof Seal';
                      setTimeout(() => {
                        stopDemo();
                      }, 5000);
                    }, 2400);
                  }, 2400);
                }, 2000);
              });
            }, 2000);
          });
        }, 2000);
      });
    }, 400);
  }

  const demoModeBtn = document.getElementById('demo-mode-btn');
  if (demoModeBtn) {
    demoModeBtn.addEventListener('click', startDemo);
  }

  const stopDemoBtn = document.getElementById('btn-stop-demo');
  if (stopDemoBtn) {
    stopDemoBtn.addEventListener('click', stopDemo);
  }
});

let currentThinkingTimer = null;
let processBarTimeout = null;

function startThinkingProcess(startTime) {
  const bar = document.getElementById('thinking-process-bar');
  const stepText = document.getElementById('thinking-bar-step');
  const timerText = document.getElementById('thinking-bar-elapsed');
  if (!bar || !stepText) return;

  if (processBarTimeout) {
    clearTimeout(processBarTimeout);
    processBarTimeout = null;
  }
  if (currentThinkingTimer) {
    clearInterval(currentThinkingTimer);
    currentThinkingTimer = null;
  }

  bar.classList.remove('hidden');
  stepText.style.color = '';

  const steps = [
    'Verifying grievance details & jurisdiction...',
    'Checking competent department & SLA requirements...',
    'Preparing formal petition & auto-filling form...'
  ];
  stepText.textContent = steps[0];
  if (timerText) timerText.textContent = '0.0s';

  let stepIdx = 0;
  currentThinkingTimer = setInterval(() => {
    const elapsedSec = ((Date.now() - startTime) / 1000).toFixed(1);
    if (timerText) timerText.textContent = `${elapsedSec}s`;

    if (Math.floor((Date.now() - startTime) / 500) > stepIdx) {
      stepIdx++;
      if (stepIdx < steps.length) {
        stepText.textContent = steps[stepIdx];
      }
    }
  }, 100);
}

function stopThinkingProcess(data, elapsedSec) {
  if (currentThinkingTimer) {
    clearInterval(currentThinkingTimer);
    currentThinkingTimer = null;
  }

  const bar = document.getElementById('thinking-process-bar');
  const stepText = document.getElementById('thinking-bar-step');
  const timerText = document.getElementById('thinking-bar-elapsed');

  if (timerText) timerText.textContent = `${elapsedSec}s`;

  if (stepText) {
    if (data.status === 'REJECTED') {
      stepText.textContent = 'Notice: Request is outside administrative grievance scope';
      stepText.style.color = 'var(--danger)';
    } else {
      stepText.textContent = 'Filing updated & formal petition prepared ✓';
      stepText.style.color = 'var(--success)';
    }
  }

  if (bar) {
    processBarTimeout = setTimeout(() => {
      bar.classList.add('hidden');
    }, 1800);
  }
}

function updateWorkflowStepper(status, isRejection = false) {
  const stepTriage = document.getElementById('step-triage');
  const stepElicit = document.getElementById('step-elicitation');
  const stepDraft = document.getElementById('step-drafting');
  const stepHitl = document.getElementById('step-hitl');
  const stepSub = document.getElementById('step-submission');

  const conn1 = document.getElementById('conn-1');
  const conn2 = document.getElementById('conn-2');
  const conn3 = document.getElementById('conn-3');
  const conn4 = document.getElementById('conn-4');

  if (!stepTriage) return;

  function setNode(node, state, labelText) {
    if (!node) return;
    node.className = 'stepper-node ' + state;
    const num = node.querySelector('.step-num');
    if (num && labelText) num.textContent = labelText;
  }

  function setLine(line, state) {
    if (!line) return;
    line.className = 'stepper-line ' + state;
  }

  if (isRejection || status === 'REJECTED') {
    setNode(stepTriage, 'rejected', '✕');
    setNode(stepElicit, '', '2');
    setNode(stepDraft, '', '3');
    setNode(stepHitl, '', '4');
    setNode(stepSub, '', '5');
    setLine(conn1, '');
    setLine(conn2, '');
    setLine(conn3, '');
    setLine(conn4, '');
    return;
  }

  if (status === 'SUBMITTED') {
    setNode(stepTriage, 'completed', '✓');
    setNode(stepElicit, 'completed', '✓');
    setNode(stepDraft, 'completed', '✓');
    setNode(stepHitl, 'completed', '✓');
    setNode(stepSub, 'completed', '✓');
    setLine(conn1, 'completed');
    setLine(conn2, 'completed');
    setLine(conn3, 'completed');
    setLine(conn4, 'completed');
  } else if (status === 'READY_FOR_DRAFT' || status === 'READY_FOR_REVIEW') {
    setNode(stepTriage, 'completed', '✓');
    setNode(stepElicit, 'completed', '✓');
    setNode(stepDraft, 'completed', '✓');
    setNode(stepHitl, 'active', '4');
    setNode(stepSub, '', '5');
    setLine(conn1, 'completed');
    setLine(conn2, 'completed');
    setLine(conn3, 'active');
    setLine(conn4, '');
  } else if (status === 'ELICITING') {
    setNode(stepTriage, 'completed', '✓');
    setNode(stepElicit, 'active', '2');
    setNode(stepDraft, '', '3');
    setNode(stepHitl, '', '4');
    setNode(stepSub, '', '5');
    setLine(conn1, 'active');
    setLine(conn2, '');
    setLine(conn3, '');
    setLine(conn4, '');
  } else {
    setNode(stepTriage, 'active', '1');
    setNode(stepElicit, '', '2');
    setNode(stepDraft, '', '3');
    setNode(stepHitl, '', '4');
    setNode(stepSub, '', '5');
    setLine(conn1, '');
    setLine(conn2, '');
    setLine(conn3, '');
    setLine(conn4, '');
  }
}

async function sendCitizenMessage(customText) {
  if (isProcessing) return;

  const userInput = document.getElementById('user-input');
  const message = (customText || (userInput ? userInput.value : '')).trim();
  if (!message) return;

  isProcessing = true;
  appendMessage('citizen', message);
  if (userInput) {
    userInput.value = '';
    userInput.disabled = true;
  }

  const startTime = Date.now();
  startThinkingProcess(startTime);

  try {
    const response = await fetch('/api/v1/agent/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentSessionId, message: message }),
    });

    const data = await response.json();

    // Subtle minimum perception pause (~500ms)
    const elapsed = Date.now() - startTime;
    if (elapsed < 500) {
      await new Promise(r => setTimeout(r, 500 - elapsed));
    }

    const finalElapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    stopThinkingProcess(data, finalElapsed);
    handleAgentResponse(data, response.status);
  } catch (err) {
    stopThinkingProcess({ status: 'ERROR' }, '0.0');
    appendMessage('agent', `Network connection error: ${err.message}`);
  } finally {
    isProcessing = false;
    if (userInput) {
      userInput.disabled = false;
      userInput.focus();
    }
  }
}

function appendMessage(sender, text, isRejection = false) {
  const container = document.getElementById('messages-container');
  if (!container) return;

  const msgEl = document.createElement('div');
  msgEl.className = `message msg-${sender} ${isRejection ? 'msg-rejected' : ''}`;

  const senderLabel = sender === 'citizen' ? 'Citizen' : (isRejection ? 'Notice' : 'Sahayta');

  msgEl.innerHTML = `
    <div class="message-sender">${senderLabel}</div>
    <div class="message-content">${formatMessageText(text)}</div>
  `;

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function handleAgentResponse(data, statusCode) {
  // Update Filing Progress Stepper
  const isRej = statusCode === 422 || data.status === 'REJECTED';
  updateWorkflowStepper(data.status, isRej);

  // Rejection Handling
  if (isRej) {
    const rejMsg = data.agent_message || data.message || 'Request cannot be processed by the public grievance portal.';
    const reason = data.reason || (data.rejection && data.rejection.reason) || '';
    const advice = data.suggested_action || (data.rejection && data.rejection.suggested_action) || '';

    const fullNotice = `${rejMsg}${reason ? '\n\n' + reason : ''}${advice ? '\n\nOfficial Advice: ' + advice : ''}`;
    appendMessage('agent', fullNotice, true);
    return;
  }

  // Update Authority & Jurisdiction Card
  if (data.grounded_data) {
    updateAuthorityCard(data.grounded_data);
  }

  // Update Browser URL & Schema Pill
  const schemaId = data.schema_id || data.portal;
  if (schemaId && portalUrlMapping[schemaId]) {
    const urlEl = document.getElementById('portal-url');
    if (urlEl) urlEl.textContent = portalUrlMapping[schemaId];
  }

  const formSchemaTag = document.getElementById('form-schema-tag');
  if (formSchemaTag) formSchemaTag.textContent = data.portal || 'CPGRAMS';

  const portalTierTag = document.getElementById('portal-tier-tag');
  if (portalTierTag) {
    portalTierTag.textContent = `${data.portal || 'GOVERNMENT'} PORTAL GATEWAY`;
  }

  // Live Automated Form Sandbox Filling
  if (data.collected_fields || data.missing_fields) {
    animateFormFilling(data.collected_fields || {}, data.missing_fields || []);
  }

  // Update Draft Petition & Auto-switch Tab
  if (data.draft) {
    currentDraft = data.draft;
    renderPetition(data.draft);
    const actionBox = document.getElementById('submit-action-box');
    if (actionBox) actionBox.classList.remove('hidden');

    // Auto-switch to Article 350 Petition tab to showcase legal drafting
    const tabPetitionBtn = document.getElementById('tab-petition-btn');
    const tabFormBtn = document.getElementById('tab-form-btn');
    const portalFormView = document.getElementById('portal-form-view');
    const petitionView = document.getElementById('petition-view');
    if (tabPetitionBtn && tabFormBtn && portalFormView && petitionView) {
      setTimeout(() => {
        tabPetitionBtn.classList.add('active');
        tabFormBtn.classList.remove('active');
        petitionView.classList.remove('hidden');
        portalFormView.classList.add('hidden');
      }, 300);
    }
  }

  // Direct Docket Receipt if completed
  if (data.receipt) {
    renderDocket(data.receipt);
  }

  // Conversational message
  const msgText = data.agent_message || data.message || data.text;
  if (msgText) {
    appendMessage('agent', msgText, false);
    speakText(msgText);
  }
}

function updateAuthorityCard(meta) {
  const tierBadge = document.getElementById('tier-badge');
  const slaBadge = document.getElementById('sla-badge');
  const authName = document.getElementById('authority-name');

  if (tierBadge) tierBadge.textContent = meta.sovereign_tier || 'Central Government';
  if (slaBadge) slaBadge.textContent = `SLA: ${meta.standard_sla_days || 30} Days`;
  if (authName) authName.textContent = meta.ministry_or_department || 'Competent Authority';

  const statuteEl = document.getElementById('meta-statute');
  const nodalEl = document.getElementById('meta-nodal');
  const officerEl = document.getElementById('meta-officer');
  const appealEl = document.getElementById('meta-appeal');

  if (statuteEl) statuteEl.textContent = meta.statutory_act || '-';
  if (nodalEl) nodalEl.textContent = meta.nodal_entity || meta.ministry_or_department || '-';
  if (officerEl) officerEl.textContent = meta.competent_officer || 'Public Grievance Officer';
  if (appealEl) appealEl.textContent = meta.escalation_avenue || 'First Appellate Authority';
}

function animateFormFilling(collected, missing) {
  const fields = [
    { id: 'field-name', val: collected.complainant_name },
    { id: 'field-mobile', val: collected.mobile_number },
    { id: 'field-email', val: collected.email },
    { id: 'field-location', val: [collected.district, collected.state, collected.pincode].filter(Boolean).join(', ') },
    { id: 'field-identifier', val: collected.ration_card_number || collected.consumer_account_number || collected.consumer_number || collected.reference_number },
    { id: 'field-department', val: collected.ministry_department || collected.utility_provider || collected.water_board_name },
    { id: 'field-category', val: collected.grievance_category || collected.issue_category },
    { id: 'field-description', val: collected.grievance_description }
  ];

  // Staggered sequential filling animation (shows agent typing into government form)
  fields.forEach((item, index) => {
    if (item.val && String(item.val).trim() !== '') {
      setTimeout(() => {
        setFieldValue(item.id, item.val);
      }, index * 60);
    }
  });

  // Highlight missing fields
  missing.forEach(field => {
    let inputId = null;
    if (field === 'complainant_name') inputId = 'field-name';
    else if (field === 'mobile_number') inputId = 'field-mobile';
    else if (field === 'email') inputId = 'field-email';
    else if (['ration_card_number', 'consumer_account_number', 'consumer_number'].includes(field)) inputId = 'field-identifier';

    if (inputId) {
      const el = document.getElementById(inputId);
      if (el && !el.value) {
        el.classList.add('missing-pulse');
        el.placeholder = 'Awaiting your voice/text reply...';
      }
    }
  });
}

function setFieldValue(elementId, val) {
  const el = document.getElementById(elementId);
  if (!el) return;

  if (val && String(val).trim() !== '') {
    el.value = String(val);
    el.classList.remove('missing-pulse');
    el.classList.add('filled');
  }
}

function renderPetition(draft) {
  const box = document.getElementById('petition-text-box');
  if (box) {
    box.textContent = draft.full_letter_text || JSON.stringify(draft, null, 2);
  }
}

function renderDocket(receipt) {
  const docket = document.getElementById('docket-card');
  if (!docket) return;

  document.getElementById('docket-tracking').textContent = receipt.tracking_number || receipt.tracking_id || '-';
  document.getElementById('docket-time').textContent = receipt.submission_timestamp_utc || '-';
  document.getElementById('docket-deadline').textContent = receipt.resolution_deadline_utc || '-';
  document.getElementById('docket-hash').textContent = receipt.tamper_evident_hash || receipt.receipt_hash || '-';
  document.getElementById('docket-advice').textContent = receipt.advice_to_citizen || '';

  docket.classList.remove('hidden');
}

function resetFormSandbox() {
  const inputs = document.querySelectorAll('.form-input');
  inputs.forEach(input => {
    input.value = '';
    input.classList.remove('filled', 'missing-pulse');
  });

  const docket = document.getElementById('docket-card');
  if (docket) docket.classList.add('hidden');

  const actionBox = document.getElementById('submit-action-box');
  if (actionBox) actionBox.classList.add('hidden');

  const petitionBox = document.getElementById('petition-text-box');
  if (petitionBox) petitionBox.textContent = 'Awaiting complete particulars to synthesize petition...';

  // Reset workflow stepper
  updateWorkflowStepper('INITIAL');

  // Reset authority card
  const tierBadge = document.getElementById('tier-badge');
  const slaBadge = document.getElementById('sla-badge');
  const authName = document.getElementById('authority-name');
  if (tierBadge) tierBadge.textContent = 'Awaiting Intake';
  if (slaBadge) slaBadge.textContent = 'SLA: Pending';
  if (authName) authName.textContent = 'Central Grievance Redressal (CPGRAMS)';

  const statuteEl = document.getElementById('meta-statute');
  const nodalEl = document.getElementById('meta-nodal');
  const officerEl = document.getElementById('meta-officer');
  const appealEl = document.getElementById('meta-appeal');
  if (statuteEl) statuteEl.textContent = '-';
  if (nodalEl) nodalEl.textContent = '-';
  if (officerEl) officerEl.textContent = '-';
  if (appealEl) appealEl.textContent = '-';

  const formSchemaTag = document.getElementById('form-schema-tag');
  if (formSchemaTag) formSchemaTag.textContent = 'CPGRAMS';

  const portalTierTag = document.getElementById('portal-tier-tag');
  if (portalTierTag) portalTierTag.textContent = 'GOVERNMENT PORTAL GATEWAY';

  const portalUrl = document.getElementById('portal-url');
  if (portalUrl) portalUrl.textContent = 'https://pgportal.gov.in/Grievance/NewFiling';

  const thinkingBar = document.getElementById('thinking-process-bar');
  if (thinkingBar) thinkingBar.classList.add('hidden');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatMessageText(text) {
  if (!text) return '';
  let safe = escapeHtml(text);
  // Bold **text**
  safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  safe = safe.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Bullets • or -
  safe = safe.replace(/\n•\s*(.*?)(?=\n|$)/g, '<br>&bull; $1');
  // Newlines to <br>
  safe = safe.replace(/\n/g, '<br>');
  return safe;
}
