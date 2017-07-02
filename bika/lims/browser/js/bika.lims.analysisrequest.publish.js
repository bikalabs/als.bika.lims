
/* Please use this command to compile this file into the parent `js` directory:
        coffee --no-header -w -o ../ -c bika.lims.analysisrequest.publish.coffee
 */

(function() {
  var mmTopx, pxTomm;

  mmTopx = function(mm) {
    var px;
    px = parseFloat(mm * $('<div style="height:1mm"/>').height());
    if (px > 0) {
      return Math.ceil(px);
    } else {
      return Math.floor(px);
    }
  };

  pxTomm = function(px) {
    var mm;
    mm = parseFloat(px / $('<div style="height:1mm"/>').height());
    if (mm > 0) {
      return Math.floor(mm);
    } else {
      return Math.ceil(mm);
    }
  };

  window.AnalysisRequestPublishView = function() {
    var applyMargin, convert_svgs, default_margins, getPaperSize, load_barcodes, load_layout, papersize_default, papersizes, referrer_cookie_name, reloadReport, that;
    that = this;
    referrer_cookie_name = '_arpv';
    papersize_default = 'A4';
    default_margins = [20, 20, 20, 20];
    papersizes = {
      'A4': {
        size: 'A4',
        dimensions: [210, 297],
        margins: [10, 10, 10, 10]
      },
      'letter': {
        size: 'letter',
        dimensions: [216, 279],
        margins: [10, 10, 10, 10]
      }
    };
    getPaperSize = function() {
      return papersizes[$('#sel_layout').val()];
    };
    applyMargin = function(element, idx) {
      var margin, maxmargin, n, papersize;
      papersize = getPaperSize();
      maxmargin = papersize.dimensions[(idx + 1) % 2] / 4;
      margin = $(element).val();
      n = ~~Number(margin);
      if (String(n) === margin && n >= 0 && n <= maxmargin) {
        papersizes[$('#sel_layout').val()].margins[idx] = n;
        $(element).val(n);
      } else {
        $(element).val(papersize.margins[idx]);
      }
    };
    load_barcodes = function() {
      $('.barcode').each(function() {
        var addQuietZone, barHeight, code, id, showHRI;
        id = $(this).attr('data-id');
        code = $(this).attr('data-code');
        barHeight = $(this).attr('data-barHeight');
        addQuietZone = $(this).attr('data-addQuietZone');
        showHRI = $(this).attr('data-showHRI');
        $(this).barcode(id, code, {
          barHeight: parseInt(barHeight),
          addQuietZone: Boolean(addQuietZone),
          showHRI: Boolean(showHRI)
        });
      });
    };
    convert_svgs = function() {
      $('svg').each(function(e) {
        var img, svg;
        svg = $('<div />').append($(this).clone()).html();
        img = window.bika.lims.CommonUtils.svgToImage(svg);
        $(this).replaceWith(img);
      });
    };
    reloadReport = function() {
      var hvisible, landscape, qcvisible, template, url;
      url = window.location.href;
      template = $('#sel_format').val();
      qcvisible = $('#qcvisible').is(':checked') ? '1' : '0';
      hvisible = $('#hvisible').is(':checked') ? '1' : '0';
      landscape = $('#landscape').is(':checked') ? '1' : '0';
      if ($('#report:visible').length > 0) {
        $('#report').fadeTo('fast', 0.4);
      }
      $.ajax({
        url: url,
        type: 'POST',
        async: true,
        data: {
          template: template,
          qcvisible: qcvisible,
          hvisible: hvisible,
          landscape: landscape
        }
      }).always(function(data) {
        var cssdata, htmldata;
        htmldata = data;
        cssdata = $(htmldata).find('#report-style').html();
        $('#report-style').html(cssdata);
        htmldata = $(htmldata).find('#report').html();
        $('#report').html(htmldata);
        $('#report').fadeTo('fast', 1);
        load_barcodes();
        load_layout();
        window.bika.lims.RangeGraph.load();
        convert_svgs();
      });
    };
    load_layout = function() {
      var dim, layout_style, orientation, papersize;
      orientation = $('#landscape').is(':checked') ? 'landscape' : 'portrait';
      papersize = getPaperSize();
      dim = {
        size: papersize.size,
        orientation: orientation,
        outerWidth: papersize.dimensions[0],
        outerHeight: papersize.dimensions[1],
        marginTop: papersize.margins[0],
        marginRight: papersize.margins[1],
        marginBottom: papersize.margins[2],
        marginLeft: papersize.margins[3],
        width: papersize.dimensions[0] - papersize.margins[1] - papersize.margins[3],
        height: papersize.dimensions[1] - papersize.margins[0] - papersize.margins[2]
      };
      $('div.ar_publish_body').each(function(i) {
        var aboveBreakHtml, accumHeight, arbody, elCurrent, elTopOffset, footer_height, footer_html, header_height, header_html, paddingTopFoot, pageBreak, pageHeight, pagecntidx, pagecounts, pagenum, pgf, pgh, split_at;
        arbody = $(this);
        header_html = '<div class="page-header"></div>';
        header_height = $(header_html).outerHeight(true);
        if (arbody.find('.page-header').length > 0) {
          pgh = arbody.find('.page-header').first();
          header_height = parseFloat($(pgh).outerHeight(true));
          if (header_height > mmTopx(dim.marginTop)) {
            dim.marginTop = pxTomm(header_height) + 2;
            $('#margin-top').val(dim.marginTop);
          }
          header_html = '<div class="page-header">' + $(pgh).html() + '</div>';
          arbody.find('.page-header').remove();
        }
        footer_html = '<div class="page-footer"></div>';
        footer_height = $(footer_html).outerHeight(true);
        if (arbody.find('.page-footer').length > 0) {
          pgf = arbody.find('.page-footer').first();
          footer_height = parseFloat($(pgf).outerHeight(true));
          if (footer_height > mmTopx(dim.marginBottom)) {
            dim.marginBottom = pxTomm(footer_height) + 2;
            $('#margin-bottom').val(dim.marginBottom);
          }
          footer_html = '<div class="page-footer">' + $(pgf).html() + '</div>';
          arbody.find('.page-footer').remove();
        }
        dim.height = papersize.dimensions[1] - dim.marginTop - dim.marginBottom;
        arbody.find('.page-break').remove();
        if (arbody.find('div').last().hasClass('manual-page-break')) {
          arbody.find('div').last().remove();
        }
        if (arbody.find('div').first().hasClass('manual-page-break')) {
          arbody.find('div').first().remove();
        }
        elTopOffset = arbody.position().top;
        pageHeight = mmTopx(dim.height);
        elCurrent = null;
        accumHeight = 0;
        pagenum = 1;
        pagecounts = Array();
        arbody.children('div:visible').each(function(z) {
          var aboveBreakHtml, div, elHeight, elTopPos, manualbreak, paddingTopFoot, pageBreak, restartcount;
          div = $(this);
          elTopPos = div.position().top - elTopOffset;
          elHeight = parseFloat(div.outerHeight(true));
          accumHeight = elTopPos + elHeight;
          if (elCurrent === null) {
            $(header_html).insertBefore(div);
            elTopOffset = div.position().top;
            elTopOffset = elTopOffset - 20;
          }
          if (elHeight > pageHeight) {
            console.warn('Element with id ' + div.attr('id') + ' has a height above the maximum: ' + elHeight);
          }
          if (accumHeight > pageHeight || div.hasClass('manual-page-break')) {
            accumHeight = div.outerHeight(true);
            paddingTopFoot = pageHeight - elTopPos;
            manualbreak = div.hasClass('manual-page-break');
            restartcount = manualbreak && div.hasClass('restart-page-count');
            aboveBreakHtml = '<div style="clear:both;margin-top:' + pxTomm(paddingTopFoot) + 'mm"></div>';
            pageBreak = '<div class="page-break' + (restartcount ? ' restart-page-count' : '') + '" data-pagenum="' + pagenum + '"></div>';
            $(aboveBreakHtml + footer_html + pageBreak + header_html).insertBefore(div);
            elTopOffset = div.position().top;
            if (manualbreak) {
              div.hide();
              if (restartcount) {
                pagecounts.push(pagenum);
                pagenum = 0;
              }
            }
            pagenum += 1;
          }
          div.css('width', '100%');
          elCurrent = div;
        });
        if (elCurrent !== null) {
          paddingTopFoot = pageHeight - accumHeight;
          aboveBreakHtml = '<div style="clear:both;margin-top:' + pxTomm(paddingTopFoot) + 'mm"></div>';
          pageBreak = '<div class="page-break" data-pagenum="' + pagenum + '"></div>';
          pagecounts.push(pagenum);
          $(aboveBreakHtml + footer_html + pageBreak).insertAfter($(elCurrent));
        }
        split_at = 'div.page-header';
        $(this).find(split_at).each(function() {
          $(this).add($(this).nextUntil(split_at)).wrapAll('<div class="ar_publish_page"/>');
        });
        $(this).find('div.page-header').each(function() {
          var baseheight;
          baseheight = $(this).height();
          $(this).css({
            height: pxTomm(baseheight) + 'mm',
            margin: 0,
            padding: pxTomm(mmTopx(dim.marginTop) - baseheight) + 'mm 0 0 0'
          });
          $(this).parent().before(this);
        });
        $(this).find('div.page-break').each(function() {
          $(this).parent().after(this);
        });
        $(this).find('div.page-footer').each(function() {
          $(this).css({
            height: dim.marginBottom + 'mm',
            margin: 0,
            padding: 0
          });
          $(this).parent().after(this);
        });
        pagenum = 1;
        pagecntidx = 0;
        $(this).find('.page-current-num,.page-total-count,div.page-break').each(function() {
          if ($(this).hasClass('page-break')) {
            if ($(this).hasClass('restart-page-count')) {
              pagenum = 1;
              pagecntidx += 1;
            } else {
              pagenum = parseInt($(this).attr('data-pagenum')) + 1;
            }
          } else if ($(this).hasClass('page-current-num')) {
            $(this).html(pagenum);
          } else {
            $(this).html(pagecounts[pagecntidx]);
          }
        });
      });
      $('#margin-top').val(dim.marginTop);
      $('#margin-right').val(dim.marginRight);
      $('#margin-bottom').val(dim.marginBottom);
      $('#margin-left').val(dim.marginLeft);
      layout_style = '@page { size:    ' + dim.size + ' ' + orientation + ' !important; margin: 0mm ' + dim.marginRight + 'mm 0mm ' + dim.marginLeft + 'mm !important;' + '}';
      $('#layout-style').html(layout_style);
      $('#ar_publish_container').css({
        width: dim.width + 'mm',
        padding: '0mm ' + dim.marginRight + 'mm 0mm ' + dim.marginLeft + 'mm '
      });
      $('#ar_publish_header').css('margin', '0mm -' + dim.marginRight + 'mm 0mm -' + dim.marginLeft + 'mm');
      $('div.ar_publish_body').css({
        width: dim.width + 'mm',
        'max-width': dim.width + 'mm',
        'min-width': dim.width + 'mm'
      });
      $('.manual-page-break').remove();
    };
    that.load = function() {
      var backurl, cookiename, invalidbackurl, provisbackurl;
      load_barcodes();
      load_layout();
      convert_svgs();
      cookiename = 'ar.publish.view.referrer';
      backurl = document.referrer;
      if (backurl) {
        createCookie(cookiename, backurl);
      } else {
        backurl = readCookie(cookiename);
        if (!backurl) {
          backurl = portal_url;
        }
      }
      $('#ar_publish_container #ar_publish_summary a[href^="#"]').click(function(e) {
        var anchor, offset;
        e.preventDefault();
        anchor = $(this).attr('href');
        offset = $(anchor).first().offset().top - 20;
        $('html,body').animate({
          scrollTop: offset
        }, 'fast');
      });
      $('#sel_format').change(function(e) {
        reloadReport();
      });
      $('#landscape').click(function(e) {
        var key, landscape;
        landscape = $('#landscape').is(':checked') ? 1 : 0;
        $('body').toggleClass('landscape', landscape);
        for (key in papersizes) {
          papersizes[key]['dimensions'].reverse();
        }
        reloadReport();
      });
      $('#qcvisible').click(function(e) {
        reloadReport();
      });
      $('#hvisible').click(function(e) {
        reloadReport();
      });
      $('#sel_layout').change(function(e) {
        $('body').removeClass($('body').attr('data-layout'));
        $('body').attr('data-layout', $(this).val());
        $('body').addClass($(this).val());
        reloadReport();
      });
      $('#publish_button').click(function(e) {
        var count, hvisible, qcvisible, template, url;
        url = window.location.href;
        qcvisible = $('#qcvisible').is(':checked') ? 1 : 0;
        hvisible = $('#hvisible').is(':checked') ? 1 : 0;
        template = $('#sel_format').val();
        $('#ar_publish_container').animate({
          opacity: 0.4
        }, 'slow');
        count = $('#ar_publish_container #report .ar_publish_body').length;
        $('#ar_publish_container #report .ar_publish_body').each(function() {
          var rephtml, repstyle;
          rephtml = $(this).clone().wrap('<div>').parent().html();
          repstyle = $('#report-style').clone().wrap('<div>').parent().html();
          repstyle += $('#layout-style').clone().wrap('<div>').parent().html();
          repstyle += $('#layout-print').clone().wrap('<div>').parent().html();
          $.ajax({
            url: url,
            type: 'POST',
            async: false,
            data: {
              publish: 1,
              id: $(this).attr('id'),
              uid: $(this).attr('uid'),
              html: rephtml,
              template: template,
              qcvisible: qcvisible,
              hvisible: hvisible,
              style: repstyle
            }
          }).always(function() {
            if (!--count) {
              location.href = backurl;
            }
          });
        });
      });
      $('#cancel_button').click(function(e) {
        location.href = backurl;
      });
      invalidbackurl = window.portal_url + '/++resource++bika.lims.images/report_invalid_back.png';
      $('.ar-invalid').css('background', 'url("' + invalidbackurl + '") repeat scroll #ffffff');
      provisbackurl = window.portal_url + '/++resource++bika.lims.images/report_provisional_back.png';
      $('.ar-provisional').css('background', 'url("' + provisbackurl + '") repeat scroll #ffffff');
      $('#sel_format_info').click(function(e) {
        e.preventDefault();
        $('#sel_format_info_pane').toggle();
      });
      $('#margin-top').change(function(e) {
        applyMargin($(this), 0);
        reloadReport();
      });
      $('#margin-right').change(function(e) {
        applyMargin($(this), 1);
        reloadReport();
      });
      $('#margin-bottom').change(function(e) {
        applyMargin($(this), 2);
        reloadReport();
      });
      $('#margin-left').change(function(e) {
        applyMargin($(this), 3);
        reloadReport();
      });
    };
  };

}).call(this);
