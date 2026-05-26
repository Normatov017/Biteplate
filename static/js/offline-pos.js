(function(){
    var queueKey = 'biteplate.offlineQueue';
    var banner = document.querySelector('[data-offline-banner]');

    function getQueue(){
        try {
            return JSON.parse(localStorage.getItem(queueKey) || '[]');
        } catch (error) {
            return [];
        }
    }

    function setQueue(queue){
        localStorage.setItem(queueKey, JSON.stringify(queue));
    }

    function updateBanner(){
        if (!banner) return;
        var queue = getQueue();
        banner.classList.toggle('is-visible', !navigator.onLine || queue.length > 0);
        banner.textContent = navigator.onLine
            ? 'Syncing ' + queue.length + ' queued POS action(s)...'
            : 'Offline mode: POS actions are queued locally.';
    }

    async function replayQueue(){
        if (!navigator.onLine) {
            updateBanner();
            return;
        }

        var queue = getQueue();
        var remaining = [];

        for (var i = 0; i < queue.length; i += 1) {
            var action = queue[i];
            var body = new URLSearchParams(action.fields);

            try {
                var response = await fetch(action.url, {
                    method: action.method,
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: body,
                    credentials: 'same-origin'
                });

                if (!response.ok) {
                    remaining.push(action);
                }
            } catch (error) {
                remaining.push(action);
            }
        }

        setQueue(remaining);
        updateBanner();

        if (queue.length > 0 && remaining.length === 0) {
            window.location.reload();
        }
    }

    document.addEventListener('submit', function(event){
        var form = event.target;

        if (!form.matches('[data-offline-queue]') || navigator.onLine) {
            return;
        }

        event.preventDefault();

        var fields = [];
        var data = new FormData(form);

        data.forEach(function(value, key){
            fields.push([key, value]);
        });

        var queue = getQueue();
        queue.push({
            url: form.action,
            method: form.method || 'POST',
            fields: fields,
            createdAt: new Date().toISOString()
        });
        setQueue(queue);
        updateBanner();
    });

    window.addEventListener('online', replayQueue);
    window.addEventListener('offline', updateBanner);
    updateBanner();
    replayQueue();
})();
