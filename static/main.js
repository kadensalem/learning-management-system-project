import { $ } from "/static/jquery/src/jquery.js";

export function say_hi(elt) {
    console.log("Say hi to", elt);
}
say_hi($("h1"));

export function make_table_sortable($table) {
    // Assign the on click event
    $('th.sortable').on( "click", function() {
        let index = $('th').index(this);
        let $header = $($('th').get(index));
        console.log(index);

        // Remove/Add appropriate class
        if($header.hasClass('sort-asc')) {
            $('th.sortable').removeClass('sort-asc sort-desc');
            $header.addClass('sort-desc');
        }
        else if($header.hasClass('sort-desc')) {
            $('th.sortable').removeClass('sort-asc sort-desc');
        }
        else {
            $('th.sortable').removeClass('sort-asc sort-desc');
            $header.addClass('sort-asc');
        }

        // Select all rows
        let $rows = $table.find('tbody tr');

        // Turn it into an array
        let arrayRows = $rows.toArray();

        // Sort if ascending
        if($header.hasClass('sort-asc')) {
            arrayRows.sort((a, b) => {
                // Convert last td element in tr to number and sort by that
                let aValue = parseFloat($(a).find('td').eq(index).data("value"));
                let bValue = parseFloat($(b).find('td').eq(index).data("value"));

                return aValue - bValue;
            });
        }

        // Sort if descending
        else if($header.hasClass('sort-desc')) {
            arrayRows.sort((a, b) => {
                // Convert last td element in tr to number and sort by that
                let aValue = parseFloat($(a).find('td').eq(index).data("value"));
                let bValue = parseFloat($(b).find('td').eq(index).data("value"));

                return bValue - aValue;
            });
        }

        // Sort original order
        else {
            arrayRows.sort((a, b) => {
                // Get index data
                let aValue = $(a).data("index");
                let bValue = $(b).data("index");

                return aValue - bValue;
            });
        }

        // Wrap arrayRows back into jQuery
        let sortedRows = $(arrayRows);

        // Append the rows back to the table
        $table.find('tbody').append(sortedRows);
    } );
}

export function make_form_async($form) {
    $form.on( "submit", function( event ) {
        // Prevent default action from happening
        event.preventDefault();

        // Disable all inputs
        $('input').prop('disabled', true);

        // Get the csrf token
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Construct form data
        let formData = new FormData();
        let file = $form.find('input[name="submittedFile"]')[0].files[0];
        formData.append("submittedFile", file);

        // Make ajax request
        $.ajax({
            url: window.location.href + "submit/",
            data: formData,
            type: "post",
            processData: false,
            contentType: false,
            mimeType: 'multipart/form-data',
            headers: {
                "X-CSRFToken": csrftoken
            },
            success: function(data) {
                $form.replaceWith("<p>Uploaded successfuly.</p>");
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log("Error submitting: " + errorThrown);
            }
        })
    });
}

export function make_grade_hypothesized($table) {
    // Add the button
    $table.before("<button id='hypoButton'>Hypothesize</button>");

    // Add the on click handler
    $('#hypoButton').on( "click", function() {
        // Go back to original state
        if($table.hasClass('hypothesized')) {
            // Remove class
            $table.removeClass('hypothesized');
            $('#hypoButton').text("Hypothesize");

            // Revert number inputs back
            let $Ungraded = $("td[data-value='Ungraded']");
            $Ungraded.each(function() {
                $(this).html("Ungraded")
            });
            let $NotDue = $("td[data-value='Not']");
            $NotDue.each(function() {
                $(this).html("Not due")
            });
        }

        // Go to hypothesize mode
        else{
            // Add class
            $table.addClass('hypothesized');
            $('#hypoButton').text("Actual Grades");

            // Change all ungraded/not due to number inputs
            let $Ungraded = $("td[data-value='Ungraded']");
            $Ungraded.each(function() {
                $(this).html("<input type='number'>")
            });
            let $NotDue = $("td[data-value='Not']");
            $NotDue.each(function() {
                $(this).html("<input type='number'>")
            });

            // Add on change handler
            $( "input" ).on( "change", function() {
                computeGrade($table);
            });
        }

        computeGrade($table);
    });
}

function computeGrade($table) {
    // Compute final grade
    let $grades = $('.grade');
    let possiblePoints = 0;
    let points = 0;
    $grades.each(function() {
        // Hypothetical input
        if(($(this).data("value") === 'Ungraded' || $(this).data("value") === 'Not')) {
            // Only run this if in hypothesis mode
            if($table.hasClass('hypothesized')) {
                let weight = parseFloat($(this).data("weight"));
                let $input = $(this).find('input');
                if($input.val() !== '') {
                    let percent = $input.val() / 100;
                    possiblePoints += weight;
                    points += weight * percent;
                    console.log(weight + '     ' + percent);
                }
            }
        }

        // Actual input
        else {
            let weight = parseFloat($(this).data("weight"));
            let percent = 0;
            
            // Missing values == 0
            if($(this).data("value") !== 'Missing') {
                percent = parseFloat($(this).data("value")) / 100;
            }

            possiblePoints += weight;
            points += weight * percent;
            console.log(weight + '     ' + percent);
        }

        let computedGrade = points / possiblePoints * 100;
        $('tfoot td.number_col').html('<strong>' + computedGrade.toFixed(1).toString() + '%</strong>')
    });
}