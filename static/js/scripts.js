$(document).ready(function() {
    const terminals = {};
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    $('#add-connection-btn').click(function() {
        $('#addConnectionModal').modal('show');
    });

    $('#add-connection-form').submit(function(event) {
        event.preventDefault();
        const host = $('#host').val();
        const port = $('#port').val();
        const username = $('#username').val();
        const password = $('#password').val();
        const pub_key = $('#pub_key').prop('files')[0];

        const formData = new FormData();
        formData.append('host', host);
        formData.append('port', port);
        formData.append('username', username);
        formData.append('password', password);
        if (pub_key) {
            formData.append('pub_key', pub_key);
        }

        $.ajax({
            url: '/connect',
            type: 'POST',
            data: JSON.stringify({
                host: host,
                port: port,
                username: username,
                password: password,
                pub_key: pub_key ? pub_key.name : null
            }),
            contentType: 'application/json',
            success: function(response) {
                if (response.status === 'connected') {
                    addConnectionTab(host);
                    $('#addConnectionModal').modal('hide');
                } else {
                    alert(response.message);
                }
            }
        });
    });

    function addConnectionTab(host) {
        const tab = $('<div class="connection-tab"></div>').text(host).append('<span class="close-tab">&times;</span>');
        tab.click(function() {
            $('.connection-tab').removeClass('active');
            tab.addClass('active');
            showTerminal(host);
        });
        tab.find('.close-tab').click(function(event) {
            event.stopPropagation();
            disconnect(host);
            tab.remove();
        });
        $('.connections').append(tab);
        showTerminal(host);
    }

    function showTerminal(host) {
        if (!terminals[host]) {
            terminals[host] = new Terminal();
            terminals[host].open(document.getElementById('terminal-container'));

            terminals[host].onData(data => {
                socket.emit('input', { host: host, command: data });
            });

            socket.on('output', function(data) {
                if (data.host === host) {
                    terminals[host].write(data.output);
                }
            });
        }

        for (let key in terminals) {
            terminals[key].element.style.display = key === host ? 'block' : 'none';
        }
    }

    function disconnect(host) {
        $.ajax({
            url: '/disconnect',
            type: 'POST',
            data: JSON.stringify({ host: host }),
            contentType: 'application/json',
            success: function(response) {
                if (response.status === 'disconnected') {
                    if (terminals[host]) {
                        terminals[host].dispose();
                        delete terminals[host];
                    }
                } else {
                    alert(response.message);
                }
            }
        });
    }
});
