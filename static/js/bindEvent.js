$(document).ready(function(){
    // $("#clickMeBtn").click(function(){
    //     alert("hello")
    // });
    $("#clickMeBtn").bind("click", clickhandler1())
});
function clickhandler1(e){
    console.log("clickHandler1")
}