$(function () {
    renew_my_wallet();
    $('#renew').on('click', function () {
        renew_my_wallet();
    });
});

function renew_my_wallet() {
    let blockchain_addr = $('#my_blockchain_addr').text();
    get_coin_amount(blockchain_addr);
}

function get_coin_amount(blockchain_addr) {
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
                $('#my_wallet_current_amount').text(response.amount)
                return parseFloat(response.amount)
            }
        },
        error: function (_, status, error) {
            console.log(`status code: ${status}`)
            console.log(`Error: ${error}`)
        }
    })
}