// function lookup(username, skill) {
//     document.getElementById('lookup-form-username-field').value = username
//     document.getElementById('lookup-form-skill-field').value = skill
//     document.getElementById('lookup-form').submit()
// }

// // this is for the 2nd player to compare against
// function lookup2(username1, username2) {

//     // transfer values from #lookup-form
//     document.getElementById('lookup-form-username-field1').value =
//         document.getElementById('lookup-form-username-field').value;
//     document.getElementById('lookup-form-skill-field1').value =
//         document.getElementById('lookup-form-skill-field').value;

//     document.getElementById('lookup-form-username-field2').value = username
//     document.getElementById('lookup-form-skill-field2').value = skill
//     document.getElementById('lookup-form2').submit()
// }
//
    

// username2 & skill2 are optional
function lookup(username1, skill1, username2, skill2) {
    console.log('javascript lookup fn is running...')
    if (username2) {
        document.getElementById('lookup-form-username-field1').value = username1;
        document.getElementById('lookup-form-skill-field1').value = skill1;
        document.getElementById('lookup-form-username-field2').value = username2;
        document.getElementById('lookup-form-skill-field2').value = skill2;
        document.getElementById('lookup-form2').submit()
    } else {
        document.getElementById('lookup-form-username-field').value = username1;
        document.getElementById('lookup-form-skill-field').value = skill1;
        document.getElementById('lookup-form').submit()
    }
}