$(".btn-decrement" ).on( "click", function( event ) {
    var input = $( this ).parent().parent().find('input')
    input.val(parseInt(input.val())-1000);
});

$(".btn-increment" ).on( "click", function( event ) {
    var input = $( this ).parent().parent().find('input')
    input.val(parseInt(input.val())+1000);
});