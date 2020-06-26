$(".btn-decrement" ).on( "click", function( event ) {
    var input = $( this ).parent().parent().find('input');
    input.val(parseInt(input.val())-1000);
    input.change();
});

$(".btn-increment" ).on( "click", function( event ) {
    var input = $( this ).parent().parent().find('input');
    input.val(parseInt(input.val())+1000);
    input.change();
});

$("input[name='start'], input[name='end']").on("change", function(){
    var form = $( this ).parents('form');
    var start = parseInt(form.find("input[name='start']").val());
    var end = parseInt(form.find("input[name='end']").val());
    var length = form.find("input[name='length']").val(end-start)
});