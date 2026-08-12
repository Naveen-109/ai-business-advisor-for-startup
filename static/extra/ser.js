const API = window.API_BASE_URL || 'http://127.0.0.1:5000';

async function sendMessage(e) {
    if (e) e.preventDefault();
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return false;

    // add user message
    const msgContainer = document.getElementById('messages');
    const userDiv = document.createElement('div');
    userDiv.className = 'user';
    userDiv.textContent = text;
    msgContainer.appendChild(userDiv);
    input.value = '';

    // add loading
    const loading = document.createElement('div');
    loading.className = 'bot';
    loading.textContent = 'Analyzing...';
    msgContainer.appendChild(loading);
    msgContainer.scrollTop = msgContainer.scrollHeight;

    try {
        // If user asked for ideas, call the ideas API directly to get 30 items
        const wantsIdeas = /\b(idea|ideas|more idea|more ideas|give me ideas|more suggestions)\b/i.test(text);
        if (wantsIdeas) {
            const ideasRes = await fetch(`${API}/api/business-ideas?q=${encodeURIComponent(text)}&count=30&page=1`);
            const ideasData = await ideasRes.json();
            loading.remove();
            if (ideasData && ideasData.ideas) {
                // render paginated list UI
                let page = ideasData.page || 1;
                const perPage = ideasData.per_page || 30;
                const total = ideasData.total || ideasData.ideas.length;

                const container = document.createElement('div');
                container.className = 'bot ideas-container';

                const title = document.createElement('div');
                title.className = 'ideas-title';
                title.innerHTML = `<strong>Business Ideas (showing ${ideasData.ideas.length} of ${total})</strong>`;
                container.appendChild(title);

                const list = document.createElement('ol');
                list.start = 1 + (page - 1) * perPage;
                ideasData.ideas.forEach(idea => {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>${idea.name}</strong>: ${idea.description}`;
                    list.appendChild(li);
                });
                container.appendChild(list);

                // simple pagination controls (only next/prev)
                const controls = document.createElement('div');
                controls.className = 'ideas-controls';
                const prev = document.createElement('button');
                prev.textContent = 'Prev';
                prev.disabled = page <= 1;
                const next = document.createElement('button');
                next.textContent = 'Next';
                next.disabled = (page * perPage) >= total;

                controls.appendChild(prev);
                controls.appendChild(next);
                container.appendChild(controls);

                msgContainer.appendChild(container);
                msgContainer.scrollTop = msgContainer.scrollHeight;

                // navigation handlers
                prev.addEventListener('click', async () => {
                    const p = Math.max(1, page - 1);
                    const r = await fetch(`${API}/api/business-ideas?q=${encodeURIComponent(text)}&count=${perPage}&page=${p}`);
                    const d = await r.json();
                    if (d.ideas) {
                        page = p;
                        list.innerHTML = '';
                        list.start = 1 + (page - 1) * perPage;
                        d.ideas.forEach(idea => {
                            const li = document.createElement('li');
                            li.innerHTML = `<strong>${idea.name}</strong>: ${idea.description}`;
                            list.appendChild(li);
                        });
                        prev.disabled = page <= 1;
                        next.disabled = (page * perPage) >= (d.total || d.ideas.length);
                    }
                });

                next.addEventListener('click', async () => {
                    const p = page + 1;
                    const r = await fetch(`${API}/api/business-ideas?q=${encodeURIComponent(text)}&count=${perPage}&page=${p}`);
                    const d = await r.json();
                    if (d.ideas && d.ideas.length>0) {
                        page = p;
                        list.innerHTML = '';
                        list.start = 1 + (page - 1) * perPage;
                        d.ideas.forEach(idea => {
                            const li = document.createElement('li');
                            li.innerHTML = `<strong>${idea.name}</strong>: ${idea.description}`;
                            list.appendChild(li);
                        });
                        prev.disabled = page <= 1;
                        next.disabled = (page * perPage) >= (d.total || d.ideas.length);
                    }
                });

                // Try to save the chat
                try{
                    fetch(`${API}/api/save-chat`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        credentials: 'same-origin',
                        body: JSON.stringify({ message: text, response: JSON.stringify(ideasData) })
                    }).catch(e=>console.warn('Save chat failed', e));
                }catch(e){console.warn('Save chat exception', e)}
                return false;
            } else {
                const botDiv = document.createElement('div');
                botDiv.className = 'bot';
                botDiv.innerHTML = 'No ideas found';
                msgContainer.appendChild(botDiv);
                msgContainer.scrollTop = msgContainer.scrollHeight;
            }
        }

        // Fallback: regular chat
        const res = await fetch(`${API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: [] })
        });
        const data = await res.json();
        loading.remove();
        const botDiv = document.createElement('div');
        botDiv.className = 'bot';
        botDiv.innerHTML = data.response ? data.response.replace(/\n/g, '<br>') : 'No response';
        msgContainer.appendChild(botDiv);
        msgContainer.scrollTop = msgContainer.scrollHeight;
        // Try to save chat to server (will require user to be logged in)
        try{
            fetch(`${API}/api/save-chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify({ message: text, response: data.response })
            }).catch(e=>console.warn('Save chat failed', e));
        }catch(e){console.warn('Save chat exception', e)}
    } catch (err) {
        loading.textContent = 'Error: unable to reach server';
        console.error(err);
    }

    return false;
}

document.getElementById('chatForm').addEventListener('submit', sendMessage);
