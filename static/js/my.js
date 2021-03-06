function show_ModalMyContent(content){
    $('#modContent').html(content);
	$('#modFrm').modal();
}
function hide_ModalMyContent(){$('#modFrm').modal('hide');}
function show_Modal(title, content, type_class){
var cnt='<div class="modal-header '+type_class+'">' +
            '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>' +
            '<h4 class="modal-title"><span class="glyphicon glyphicon-warning-sign"></span>'+title+'</h4>' +
        '</div>' +
        '<div class="modal-body">'+content+'</div>' +
        '<div class="modal-footer"><button type="button" class="btn btn-default" data-dismiss="modal">Закрыть</button></div>';
	show_ModalMyContent(cnt);
}

function showErr(errContent) {show_Modal('Ошибка', errContent, 'warning');}
function showSuccess(errContent) {show_Modal('Успешно', errContent, 'success');}
function showPrimary(errContent) {show_Modal('Внимание!', errContent, 'primary');}

$(document).ajaxError(function (ev, jqXHR, ajaxSettings, thrownError) {
	showErr(jqXHR.status + ': ' + jqXHR.responseText);
});


// SelectAjax
(function ($) {
	$.fn.selectajax = function (opt) {

		var settings = $.extend( {
			url		 : this.attr('data-dst')
		}, opt);

		var selectbtn = this.children('button.selectajax-btn');
		var selectinp = this.children('input[type=text].selectajax-inp');
		var selecthid = this.children('input[type=hidden].selectajax-hid');
		var selectul  = this.children('ul.selectajax-ul');

		var selectajax_click = function(){
			var a = $(this).children('a');
			var hr = a.attr('href');
			var tx = a.text();
			selecthid.val(hr.substr(1));
			selectbtn.text(tx).removeClass('hidden');
			selectinp.addClass('hidden').val(tx);
		};

		var refresh = function(){
			$.getJSON(settings.url, {'s': this.value}, function (r) {
				selectul.empty();
				r.forEach(function (o) {
					var li = $('<li><a href="#' + o.id + '">' + o.text + '</a></li>');
					selectul.append(li);
					li.on('click', selectajax_click)
				});
			});
		};

		selectinp.on('keyup', refresh).on('focusin',refresh);

		selectbtn.on('click',function(){
			selectinp.removeClass('hidden');
			$(this).addClass('hidden');
			selectinp.focus().trigger('click.bs.dropdown');
			return false;
		});

		selectul.children().on('click', selectajax_click);
	};
})(jQuery);


// AudioPlayer
(function ($) {
	$.fn.aplayer = function(){

		var def_play = function(e){
			var audiotag = e.data['audiotag'][0];

			if(audiotag.readyState === 0){
				$(this).prop('disabled', true);
				return;
			}else
				$(this).prop('disabled', false);

			if(audiotag.paused)
                audiotag.play();
            else
                audiotag.pause();
		};

		var def_canplay = function(){
			var els = $(this).parent();
			els.prop('disabled', false).removeClass('disabled');
			els.siblings().prop('disabled', false).removeClass('disabled');
		};

		var def_on_play = function(){
			$(this).siblings('span.glyphicon').attr('class', 'glyphicon glyphicon-pause');
        };

		var def_on_pause = function(){
			$(this).siblings('span.glyphicon').attr('class', 'glyphicon glyphicon-play');
        };

		this.each(function(){
			var i = $(this);
			var audiotag = i.children('audio');
			var icon = i.children('span.glyphicon');
			i.on('click', {'audiotag': audiotag}, def_play);
			audiotag.on('canplay', def_canplay);
			audiotag.on('play', def_on_play);
			audiotag.on('pause', def_on_pause);
		});

	};
})(jQuery);


// Ajax Loader
(function ($){
    $.fn.ajloader = function(opt){
        var settings = $.extend({
			dst_block	:'id_block_obj'
		}, opt);

		var fill_block_fn = function(){
		    var url = $(this).attr('data-href');
		    $.get(url, function(r){
		        $(settings.dst_block).html(r);
		    });
		};

        this.each(function(){
			$(this).on('click', fill_block_fn);
		});
    };
})(jQuery);


// Ajax form
(function ($){
    $.fn.ajform = function(opt){
    	var on_response_default = function(){
            alert('You must assign callback function for response');
        };

        var settings = $.extend({
			on_response	: on_response_default
		}, opt);

        var on_submit = function(e){
            e.preventDefault();
            var formData = new FormData(this);
            $.ajax({
                url: $(this).attr('action'),
                type: 'POST',
                data: formData,
                async: true,
                success: settings.on_response,
                cache: false,
                contentType: false,
                processData: false
            });
        };

        this.each(function(){
			$(this).on('submit', on_submit);
		});
    };
})(jQuery);


$(document).ready(function () {

	// Live html5 image preview
	if (window.File && window.FileReader && window.FileList && window.Blob) {
		$('input[type=file].live_review').on('change', function () {
			var reader = new FileReader();
			var img = $('img[alt=ava]')[0];
			reader.readAsDataURL(this.files[0]);
			reader.onload = function (e) {
				img.src = e.target.result;
			}
		});
	} else {
		var t = "Ваш браузер не поддерживает FileAPI";
		console.warn(t);
		alert(t);
	}


	// Validate inputs of form
	$('input.form-control[pattern]').keyup(function () {
		var pr = $(this).closest('.form-group-sm,.form-group');
		pr.removeClass('has-success');
		pr.removeClass('has-error');
		pr.find('.form-control-feedback').remove();
		if ($(this)[0].checkValidity()) {
			pr.addClass('has-success');
		} else {
			pr.addClass('has-error');
		}
	});


	$('div.selectajax').selectajax();

	$('[data-toggle=offcanvas]').click(function () {
		$('.row-offcanvas').toggleClass('active');
	});

    $('.btn-modal').on('click', function(){
        $.get(this.href, function(response){
        console.log(response);
            try{
                var r = $.parseJSON(response);
                console.log(r.text);
                window.location.replace(r.url);
            }catch (e){
                show_ModalMyContent(response);
            }
        });
        return false;
    });

	// button that send command and return response of that
	$('.btn-cmd').on('click', function(){
		var cmd_param = $(this).attr('data-param');
		var form_val = $(this).attr('data-form-val');
		var self = $(this);
		self.removeClass('btn-default');
        self.removeClass('btn-danger');
        self.removeClass('btn-success');
		self.addClass('btn-info');
		self.html('<span class="glyphicon glyphicon-refresh"></span> Подождите...');
		$.getJSON(this.href, {cmd_param: cmd_param}, function(r){
            self.removeClass('btn-info');
			if(r.status == 0)
				self.addClass('btn-success');
			else
                self.addClass('btn-danger');
            self.html(r.dat);
            if(form_val){
            	$(form_val).val(r.extra_form_val);
			}
		});
		return false;
	});

	// autosave checkbox
	$('input[type=checkbox].autosave').on('click', function(){
		var data_url = $(this).attr('data-url');
		$.getJSON(data_url, {checked: this.checked});
	});

	$('button.player-btn').aplayer();

	$('[data-toggle="tooltip"]').tooltip({container:'body'});

	$('.btn_ajloader').ajloader({'dst_block': '#id_block_devices'});
});
