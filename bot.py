async function executeRobokassaCheckout() {
            if (cart.length === 0) return alert('Корзина пуста!');
            if (!currentUser) { alert('Необходимо авторизоваться.'); toggleCart(); openAuthModal('login'); return; }

            const street = document.getElementById('deliveryStreet').value.trim();
            const house = document.getElementById('deliveryHouse').value.trim();
            const apartment = document.getElementById('deliveryApartment').value.trim();
            const floor = document.getElementById('deliveryFloor').value.trim();

            if (!street || !house) {
                alert('Пожалуйста, заполните улицу и номер дома для доставки!');
                return;
            }

            let orderItemsText = cart.map(i => `• ${i.name} (x${i.quantity}) - ${Math.round(i.price * 0.85)} ₽`).join('\n');
            let totalSum = cart.reduce((sum, i) => sum + Math.round(i.price * 0.85 * i.quantity), 0);

            let message = `🔥 <b>НОВЫЙ ЗАКАЗ В МАГАЗИНЕ!</b>\n\n` +
                          `👤 <b>Клиент:</b> ${currentUser.name}\n` +
                          `📞 <b>Телефон:</b> ${currentUser.phone}\n` +
                          `📧 <b>Email:</b> ${currentUser.email}\n\n` +
                          `📍 <b>Адрес доставки:</b>\n` +
                          `Ул. ${street}, д. ${house}` + (apartment ? `, кв. ${apartment}` : '') + (floor ? `, этаж ${floor}` : '') + `\n\n` +
                          `🛒 <b>Состав заказа:</b>\n${orderItemsText}\n\n` +
                          `💰 <b>Итого к оплате:</b> ${totalSum} ₽`;

            // Ссылка на официальное API Telegram через прокси-сервер, обходящий блокировку браузера
            const telegramUrl = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`;
            const proxyUrl = 'https://corsproxy.io/?' + encodeURIComponent(telegramUrl);

            try {
                let response = await fetch(proxyUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        chat_id: TELEGRAM_CHAT_ID,
                        text: message,
                        parse_mode: 'HTML'
                    })
                });

                let data = await response.json();
                if (!data.ok) {
                    console.error('Ошибка от Telegram:', data);
                    alert('Ошибка при отправке в Telegram: ' + (data.description || 'Неизвестная ошибка'));
                    return;
                }
            } catch (err) {
                console.error('Ошибка сети:', err);
                alert('Не удалось отправить заказ. Проверьте подключение к интернету.');
                return;
            }

            alert('[ТЕСТУЕМЫЙ ПЛАТЕЖ] Заказ успешно отправлен в Telegram!');
            cart = []; 
            updateCartBadge(); 
            toggleCart();
        }
