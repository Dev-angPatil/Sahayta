// src/sahayta/static/app.js
// Interactive frontend controller for Project Sahayta

let currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 10);
let activePortal = null;
let currentDraft = null;

const portalMetadata = {
  'CPGRAMS': {
    name: 'CPGRAMS Central Public Grievance Portal',
    authority: 'DARPG, Government of India',
    statute: "Article 350 / Citizen's Charter Standard (60 Days Resolution)",
    color: '#f97316',
  },
  'GOVTECH_CPGRAMS_V1': {
    name: 'CPGRAMS Central Public Grievance Portal',
    authority: 'DARPG, Government of India',
    statute: "Article 350 / Citizen's Charter Standard (60 Days Resolution)",
    color: '#f97316',
  },
  'STATE_PDS': {
    name: 'State Public Distribution System (PDS / Ration)',
    authority: 'Food & Civil Supplies Dept, State Govt',
    statute: 'National Food Security Act (NFSA) 2013, Section 15 & 16',
    color: '#22c55e',
  },
  'STATE_PDS_V1': {
    name: 'State Public Distribution System (PDS / Ration)',
    authority: 'Food & Civil Supplies Dept, State Govt',
    statute: 'National Food Security Act (NFSA) 2013, Section 15 & 16',
    color: '#22c55e',
  },
  'DISCOM_POWER': {
    name: 'State Electricity Distribution Company (DISCOM)',
    authority: 'State Electricity Regulatory Commission',
    statute: 'Electricity Act 2003, Section 42(5) (CGRF Norms)',
    color: '#eab308',
  },
  'DISCOM_POWER_V1': {
    name: 'State Electricity Distribution Company (DISCOM)',
    authority: 'State Electricity Regulatory Commission',
    statute: 'Electricity Act 2003, Section 42(5) (CGRF Norms)',
    color: '#eab308',
  },
  'WATER_BOARD': {
    name: 'Municipal Water Supply & Sewerage Board',
    authority: 'City Jal Board / Municipal Corporation',
    statute: 'Citizen Charter for Potable Water & Sanitary Drainage',
    color: '#38bdf8',
  },
  'MUNICIPAL_WATER_V1': {
    name: 'Municipal Water Supply & Sewerage Board',
    authority: 'City Jal Board / Municipal Corporation',
    statute: 'Citizen Charter for Potable Water & Sanitary Drainage',
    color: '#38bdf8',
  },
};

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('session-badge').textContent = `Session: ${currentSessionId}`;

  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const submitBtn = document.getElementById('confirm-submit-btn');
  const newSessionBtn = document.getElementById('new-session-btn');

  // Voice Input Mode (Web Speech API)
  const voiceBtn = document.getElementById('voice-btn');
  const voiceLabel = document.getElementById('voice-label');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    if (voiceBtn) {
      voiceBtn.title = 'Speech recognition requires Chrome, Edge, or Safari';
      voiceBtn.addEventListener('click', () => {
        alert('Voice input requires a browser that supports the Web Speech API (such as Chrome, Edge, or Safari).');
      });
    }
  } else if (voiceBtn) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'hi-IN'; // Recognizes Hindi, Hinglish, and English
    let isListening = false;

    voiceBtn.addEventListener('click', () => {
      if (isListening) {
        recognition.stop();
      } else {
        try {
          recognition.start();
        } catch (err) {
          console.warn('Speech recognition start error:', err);
        }
      }
    });

    recognition.onstart = () => {
      isListening = true;
      voiceBtn.classList.add('listening');
      if (voiceLabel) voiceLabel.textContent = 'Listening...';
      userInput.placeholder = 'Listening... Speak in Hindi, English, or Hinglish...';
    };

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      if (transcript) {
        userInput.value = transcript;
      }
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      resetVoice();
    };

    recognition.onend = () => {
      resetVoice();
      if (userInput.value.trim()) {
        userInput.focus();
      }
    };

    function resetVoice() {
      isListening = false;
      voiceBtn.classList.remove('listening');
      if (voiceLabel) voiceLabel.textContent = 'Voice';
      userInput.placeholder = 'Type or speak your grievance (e.g., cancelled train refund, ration denial, power outage)...';
    }
  }

  // Handle enter key in textarea
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event('submit'));
    }
  });

  // Handle chat submission
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    appendMessage('citizen', message);
    userInput.value = '';
    userInput.disabled = true;

    try {
      const response = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, message: message }),
      });

      const data = await response.json();
      handleAgentResponse(data, response.status);
    } catch (err) {
      appendMessage('agent', `Network error: ${err.message}`);
    } finally {
      userInput.disabled = false;
      userInput.focus();
    }
  });

  // Handle direct petition submission confirmation
  submitBtn.addEventListener('click', async () => {
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting to Portal...';

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
        renderReceipt(data.receipt);
        appendMessage('agent', `Grievance submitted successfully! Reference: ${data.receipt.tracking_number}`);
        document.getElementById('draft-container').classList.add('hidden');
      } else {
        alert(data.detail || 'Submission failed. Please check required fields.');
      }
    } catch (err) {
      alert(`Error submitting grievance: ${err.message}`);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
        <span>Lodge Grievance & Execute Filing</span>
      `;
    }
  });

  // New Session handler
  newSessionBtn.addEventListener('click', () => {
    currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 10);
    activePortal = null;
    currentDraft = null;
    document.getElementById('session-badge').textContent = `Session: ${currentSessionId}`;

    // Clear messages (keep welcome)
    const container = document.getElementById('messages-container');
    const welcome = container.querySelector('.system-welcome');
    container.innerHTML = '';
    if (welcome) container.appendChild(welcome);

    // Reset dossier
    document.getElementById('portal-badge').textContent = 'No Portal Mapped';
    document.getElementById('portal-badge').className = 'portal-pill neutral';
    document.getElementById('fields-matrix').innerHTML = '<p class="empty-hint">Extracted parameters will appear here as you chat.</p>';
    document.getElementById('draft-container').classList.add('hidden');
    document.getElementById('receipt-card').classList.add('hidden');

    const emptyHint = document.querySelector('#portal-details-card .empty-hint');
    if (emptyHint) emptyHint.classList.remove('hidden');
    const infoBody = document.getElementById('portal-info-body');
    if (infoBody) infoBody.classList.add('hidden');

    userInput.focus();
  });
});

function appendMessage(sender, text, isRejection = false, reasoningTrace = null) {
  const container = document.getElementById('messages-container');
  const msgEl = document.createElement('div');
  msgEl.className = `message msg-${sender} ${isRejection ? 'msg-rejected' : ''}`;

  const senderLabel = sender === 'citizen' ? 'Citizen' : (isRejection ? 'Gate 0 Security Guardrail' : 'Sahayta Navigator');

  let traceHtml = '';
  if (reasoningTrace && reasoningTrace.length > 0) {
    const traceItems = reasoningTrace.map(step => `<div class="trace-step">${escapeHtml(step)}</div>`).join('');
    traceHtml = `
      <details class="reasoning-trace">
        <summary class="trace-summary">🧠 Agent Reasoning Pipeline (${reasoningTrace.length} steps)</summary>
        <div class="trace-body">${traceItems}</div>
      </details>
    `;
  }

  // Build message content
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';

  if (sender === 'agent' && !isRejection) {
    // Typing animation for agent messages
    msgEl.innerHTML = `
      <div class="message-sender">${senderLabel}</div>
      <div class="message-content"><span class="typing-dots">●●●</span></div>
      ${traceHtml}
    `;
    container.appendChild(msgEl);
    container.scrollTop = container.scrollHeight;

    // Reveal after short delay
    setTimeout(() => {
      const content = msgEl.querySelector('.message-content');
      content.innerHTML = escapeHtml(text);
      content.style.animation = 'fadeInText 0.3s ease-out';
      container.scrollTop = container.scrollHeight;
    }, 400);
  } else {
    msgEl.innerHTML = `
      <div class="message-sender">${senderLabel}</div>
      <div class="message-content">${escapeHtml(text)}</div>
      ${traceHtml}
    `;
    container.appendChild(msgEl);
    container.scrollTop = container.scrollHeight;
  }
}

function handleAgentResponse(data, statusCode) {
  if (statusCode === 422 || data.status === 'REJECTED') {
    const rejMsg = data.agent_message || data.message || 'Request rejected by civic guardrails.';
    const reason = data.reason || (data.rejection && data.rejection.reason) || '';
    const advice = data.suggested_action || (data.rejection && data.rejection.suggested_action) || '';

    const fullNotice = `[REJECTION: ${data.rejection_code || 'INVALID_ENTITY'}]\n${rejMsg}\n\nGround: ${reason}\n\nLegitimate Avenue: ${advice}`;
    appendMessage('agent', fullNotice, true, data.reasoning_trace);
    return;
  }

  // Update portal detection
  const portalKey = data.schema_id || data.portal;
  if (portalKey) {
    updatePortalCard(portalKey);
  }

  // Update field matrix
  if (data.collected_fields || data.missing_fields) {
    updateFieldMatrix(data.collected_fields || {}, data.missing_fields || []);
  }

  // Handle draft petition
  if (data.draft) {
    currentDraft = data.draft;
    renderDraft(data.draft);
  }

  // Handle direct receipt if returned via chat
  if (data.receipt) {
    renderReceipt(data.receipt);
    document.getElementById('draft-container').classList.add('hidden');
  }

  // Append conversational message with reasoning trace
  if (data.agent_message) {
    appendMessage('agent', data.agent_message, false, data.reasoning_trace);
  }
}

function updatePortalCard(portalKey) {
  activePortal = portalKey;
  const badge = document.getElementById('portal-badge');
  const meta = portalMetadata[portalKey] || {
    name: portalKey,
    authority: 'Designated Public Authority',
    statute: "Constitution of India / Citizen's Charter",
    color: '#38bdf8',
  };

  badge.textContent = meta.name.split('(')[0].trim();
  badge.className = 'portal-pill active';
  badge.style.background = `${meta.color}20`;
  badge.style.color = meta.color;
  badge.style.borderColor = `${meta.color}50`;

  const emptyHint = document.querySelector('#portal-details-card .empty-hint');
  if (emptyHint) emptyHint.classList.add('hidden');

  const infoBody = document.getElementById('portal-info-body');
  infoBody.classList.remove('hidden');

  document.getElementById('portal-name').textContent = meta.name;
  document.getElementById('portal-auth').textContent = meta.authority;
  document.getElementById('portal-statute').textContent = meta.statute;
}

function updateFieldMatrix(collected, missing) {
  const container = document.getElementById('fields-matrix');
  container.innerHTML = '';

  const collectedEntries = Object.entries(collected);
  if (collectedEntries.length === 0 && missing.length === 0) {
    container.innerHTML = '<p class="empty-hint">Extracted parameters will appear here.</p>';
    return;
  }

  collectedEntries.forEach(([key, val]) => {
    const item = document.createElement('div');
    item.className = 'field-item verified';
    item.style.animation = 'fieldSlideIn 0.3s ease-out';
    item.innerHTML = `
      <span class="field-name">${formatFieldLabel(key)}:</span>
      <span class="field-val">${escapeHtml(String(val))} ✓</span>
    `;
    container.appendChild(item);
  });

  missing.forEach((field) => {
    const item = document.createElement('div');
    item.className = 'field-item missing';
    item.innerHTML = `
      <span class="field-name">${formatFieldLabel(field)}:</span>
      <span class="field-val">Required (Awaiting response)</span>
    `;
    container.appendChild(item);
  });
}

function renderDraft(draft) {
  const container = document.getElementById('draft-container');
  const preview = document.getElementById('draft-text-preview');

  preview.textContent = draft.full_letter_text || JSON.stringify(draft, null, 2);
  container.classList.remove('hidden');
  container.style.animation = 'fadeInText 0.4s ease-out';
}

function renderReceipt(receipt) {
  const card = document.getElementById('receipt-card');
  document.getElementById('receipt-tracking').textContent = receipt.tracking_number || receipt.tracking_id || '-';
  document.getElementById('receipt-time').textContent = receipt.submission_timestamp_utc || '-';
  document.getElementById('receipt-deadline').textContent = receipt.resolution_deadline_utc || '-';
  document.getElementById('receipt-hash').textContent = receipt.tamper_evident_hash || receipt.receipt_hash || '-';
  document.getElementById('receipt-advice').textContent = receipt.advice_to_citizen || '';

  card.classList.remove('hidden');
  // Smooth reveal animation
  card.style.animation = 'receiptReveal 0.5s ease-out';
}

function formatFieldLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
