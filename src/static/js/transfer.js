$(function () {
    reload_amount();

    $('#submit-btn').on('click', function (e) {
        e.preventDefault();

        let decision = confirm('정말로 이체하시겠습니까?')

        if (decision) {
            let send_string = $('#transfer-form').serialize()
            $.ajax({
                url: '/transfer',
                type: 'post',
                data: send_string,
                dataType: 'json',
                success: function (response) {
                    if (response.status == 'success') {
                        alert('이체 성공했습니다!');

                        $('#form-area').attr('hidden', true);
                        $('#success-msg').text(`${response.amount} 코인 이체에 성공했습니다.`)
                        $('#after-transfer').attr('hidden', false)

                        reload_amount()
                    }

                    if (response.status == 'fail') {
                        if (response.amount == 'not_enough') {
                            alert(`이체하려는 금액이 잔액보다 커서 보낼수 없습니다.\n이체 수량을 확인해 주세요`)
                        }
                    }

                    if (response.status == 'fail') {
                        if (response.reason) {
                            alert(`${response.reason}`)
                        }
                    }
                },
                error: function (_, status, error) {
                    console.log(status)
                    console.log(error)
                }
            })
        }
    })
})

function reload_amount() {
    let blockchain_addr = $('#send_addr').val();
    let send_data = {
        'blockchain_addr': blockchain_addr
    }

    $.ajax({
        url: "/get_coin_amount",
        type: 'get',
        data: send_data,
        dataType: 'json',
        success: function (response) {
            if (response.status == 'success') {
                $('#current_coin_amount').val(response.amount)
            }
        },
        error: function (_, status, error) {
            console.log(`status code: ${status}`)
            console.log(`Error: ${error}`)
        }
    })
}

