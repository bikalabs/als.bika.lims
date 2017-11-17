### Please use this command to compile this file into the parent `js` directory:
        coffee --no-header -w -o ../ -c bika.lims.analysisrequest.publish.coffee
###

# IMPORTANT
# Please note that only first-level div elements from within div.ar_publish_body
# are checked and will be treated as nob-breakable elements. So , if a div
# element from within a div.ar_publish_body is taller than the maximum allowed
# height , that element will be omitted. Further improvements may solve this
# and handle deeply elements from the document , such as tables , etc. Other
# elements could be then labeled with "no-break" class to prevent the system
# to break them.

# This uses the css outerHeight of the top-level div elements to calculate
# pagination. This means that non-div elements will not be accounted for. All
# content must be wrapped in a <div/>!

mmTopx = (mm) ->
    px = mm * 3.779527559055
    if px > 0 then Math.ceil(px) else Math.floor(px)

pxTomm = (px) ->
    mm = px / 3.779527559055
    if mm > 0 then Math.floor(mm) else Math.ceil(mm)

#
# Controller class for AnalysisRequest publish view
#

window.AnalysisRequestPublishView = ->
    that = this
    referrer_cookie_name = '_arpv'

    # Allowed Paper sizes and default margins, in mm
    papersize_default = 'A4'
    default_margins = [20, 20, 20, 20]
    papersizes =
        'A4':
            size: 'A4'
            dimensions: [210, 297]
            margins: [10, 10, 10, 10]
        'letter':
            size: 'letter'
            dimensions: [216, 279]
            margins: [10, 10, 10, 10]

    getPaperSize = ->
        return papersizes[$('#sel_layout').val()]

    applyMargin = (element, idx) ->
        papersize = getPaperSize()
        # Maximum margin (1/4 of the total width)
        maxmargin = papersize.dimensions[(idx + 1) % 2] / 4
        margin = $(element).val()
        # Using the double-negative below because it converts NaN to 0.
        n = ~ ~Number(margin)
        if String(n) == margin and n >= 0 and n <= maxmargin
            papersizes[$('#sel_layout').val()].margins[idx] = n
            $(element).val n
        else
            # out of bounds
            $(element).val papersize.margins[idx]
        return

    load_barcodes = ->
        # Barcode generator
        $('.barcode').each ->
            id = $(this).attr('data-id')
            code = $(this).attr('data-code')
            barHeight = $(this).attr('data-barHeight')
            addQuietZone = $(this).attr('data-addQuietZone')
            showHRI = $(this).attr('data-showHRI')
            $(this).barcode id, code,
                barHeight: parseInt(barHeight)
                addQuietZone: Boolean(addQuietZone)
                showHRI: Boolean(showHRI)
            return
        return

    convert_svgs = ->
        $('svg').each (e) ->
            svg = $('<div />').append($(this).clone()).html()
            img = window.bika.lims.CommonUtils.svgToImage(svg)
            $(this).replaceWith img
            return
        return

    # Re-load the report view in accordance to the values set in  options panel
    reloadReport = ->
        url = window.location.href
        template = $('#sel_format').val()
        qcvisible = if $('#qcvisible').is(':checked') then '1' else '0'
        hvisible = if $('#hvisible').is(':checked') then '1' else '0'
        landscape = if $('#landscape').is(':checked') then '1' else '0'
        if $('#report:visible').length > 0
            $('#report').fadeTo 'fast', 0.4
        $.ajax(
            url: url
            type: 'POST'
            async: true
            data:
                template: template
                qcvisible: qcvisible
                hvisible: hvisible
                landscape: landscape
        ).always (data) ->
            htmldata = data
            cssdata = $(htmldata).find('#report-style').html()
            $('#report-style').html cssdata
            htmldata = $(htmldata).find('#report').html()
            $('#report').html htmldata
            $('#report').fadeTo 'fast', 1
            load_barcodes()
            load_layout()
            window.bika.lims.RangeGraph.load()
            convert_svgs()
            return
        return

    # Applies the selected layout (A4, US-letter) to the reports view,
    # splits each report in pages depending on the layout and margins
    # and applies the dynamic footer and/or header if required.
    # In fact, this method makes the html ready to be printed to PDF.
    load_layout = ->
        # Set page layout (DIN-A4, US-letter, etc.)
        orientation = if $('#landscape').is(':checked') then 'landscape' else 'portrait'
        # Dimensions. All expressed in mm
        papersize = getPaperSize()
        dim =
            size: papersize.size
            orientation: orientation
            outerWidth: papersize.dimensions[0]
            outerHeight: papersize.dimensions[1]
            marginTop: papersize.margins[0]
            marginRight: papersize.margins[1]
            marginBottom: papersize.margins[2]
            # first page
            firstMarginBottom: papersize.margins[2]
            marginLeft: papersize.margins[3]
            width: papersize.dimensions[0] - (papersize.margins[1]) - (papersize.margins[3])
            height: papersize.dimensions[1] - (papersize.margins[0]) - (papersize.margins[2])
            # first page
            firstHeight: papersize.dimensions[1] - (papersize.margins[0]) - (papersize.margins[2])

        # Iterate over AR reports and apply the dimensions, header, footer, etc.
        $('div.ar_publish_body').each (i) ->
            arbody = $(this)

            # Note that if the header of the report is taller than the
            # margin, the margin is increased
            header_html = '<div class="page-header"></div>'
            height = $(header_html).outerHeight(true)
            if arbody.find('.page-header').length > 0
                pgh = arbody.find('.page-header').first()
                height = parseFloat($(pgh).outerHeight(true))
                if height > mmTopx(dim.marginBottom)
                    dim.marginTop = pxTomm(height) + 5
                    dim.height = papersize.dimensions[1] - (dim.marginTop) - (dim.marginBottom)
                    $('#margin-top').val dim.marginTop
                header_html = '<div class="page-header">' + $(pgh).html() + '</div>'
                arbody.find('.page-header').remove()

            # Note that if the footer of the report is taller than the
            # margin, the margin is increased
            footer_html = '<div class="page-footer"></div>'
            height = $(footer_html).outerHeight(true)
            if arbody.find('.page-footer').length > 0
                pgf = arbody.find('.page-footer').first()
                height = parseFloat($(pgf).outerHeight(true))
                if height > mmTopx(dim.marginBottom)
                    dim.marginBottom = pxTomm(height) + 5
                    dim.height = papersize.dimensions[1] - (dim.marginTop) - (dim.marginBottom)
                    $('#margin-bottom').val dim.marginBottom
                footer_html = '<div class="page-footer">' + $(pgf).html() + '</div>'
                arbody.find('.page-footer').remove()

            # Maybe a different footer is defined for the first page:
            # If it does not fit the margin, the first page margin is increased
            first_footer_html = '<div class="first-page-footer"></div>'
            height = $(first_footer_html).outerHeight(true)
            if arbody.find('.first-page-footer').length > 0
                pgf = arbody.find('.first-page-footer').first()
                height = parseFloat($(pgf).outerHeight(true))
                if height > mmTopx(dim.firstMarginBottom)
                    dim.firstMarginBottom = pxTomm(height) + 6
                    dim.firstHeight = papersize.dimensions[1] - (dim.marginTop) - (dim.firstMarginBottom)
                first_footer_html = '<div class="first-page-footer">' + $(pgf).html() + '</div>'
                arbody.find('.first-page-footer').remove()
            else
                first_footer_html = footer_html

            # Remove undesired and orphan page breaks
            arbody.find('.page-break').remove()
            if arbody.find('div').last().hasClass('manual-page-break')
                arbody.find('div').last().remove()
            if arbody.find('div').first().hasClass('manual-page-break')
                arbody.find('div').first().remove()

            # Top offset by default. The position in which the report
            # starts relative to the top of the window. Used later to
            # calculate when a page-break is needed.
            elTopOffset = arbody.position().top
            elCurrent = null
            accumHeight = 0
            pagenum = 1
            pagecounts = Array()

            # Iterate through all div children to find the suitable
            # page-break points, split the report and add the header
            # and footer as well as pagination count as required.
            arbody.children('div:visible').each (z) ->
                div = $(this)
                if pagenum == 1
                    pageHeight = mmTopx(dim.firstHeight)
                else
                    pageHeight = mmTopx(dim.height)
                elTopPos = div.position().top - elTopOffset
                elHeight = parseFloat(div.outerHeight(true))
                accumHeight = elTopPos + elHeight
                # Is the first page?
                if elCurrent == null
                    # Add page header if required
                    $(header_html).insertBefore div
                    elTopOffset = div.position().top
                    # XXX The first page (in PDF) bleeds over to the next page.
                    # Since I can't figure out why, I compensate here manually.
                    elTopOffset = elTopOffset - 100
                # The current element is taller than the maximum?
                if elHeight > pageHeight
                    console.warn 'Element with id ' + div.attr('id') + ' has a height above the maximum: ' + elHeight

                if accumHeight > pageHeight or div.hasClass('manual-page-break')
                    # The content is taller than the allowed height
                    # or a manual page break reached. Add a page break.
                    accumHeight = div.outerHeight(true)
                    paddingTopFoot = pageHeight - elTopPos
                    manualbreak = div.hasClass('manual-page-break')
                    restartcount = manualbreak and div.hasClass('restart-page-count')
                    aboveBreakHtml = '<div style="clear:both;padding-top:' + pxTomm(paddingTopFoot) + 'mm"></div>'
                    pageBreak = '<div class="page-break' + (if restartcount then ' restart-page-count' else '') + '" data-pagenum="' + pagenum + '"></div>'
                    if pagenum == 1
                        foot = first_footer_html
                    else
                        foot = footer_html
                    $(aboveBreakHtml + foot + pageBreak + header_html).insertBefore div
                    elTopOffset = div.position().top
                    if manualbreak
                        div.hide()
                        if restartcount
                            # The page count needs to be restarted!
                            pagecounts.push pagenum
                            pagenum = 0
                    pagenum += 1
                div.css 'width', '100%'
                elCurrent = div
                return

            # Document end-footer
            if elCurrent != null
                pageHeight = mmTopx(dim.height)
                paddingTopFoot = pageHeight - accumHeight
                aboveBreakHtml = '<div style="clear:both;padding-top:' + pxTomm(paddingTopFoot) + 'mm"></div>'
                pageBreak = '<div class="page-break" data-pagenum="' + pagenum + '"></div>'
                pagecounts.push pagenum
                $(aboveBreakHtml + footer_html + pageBreak).insertAfter $(elCurrent)
            # Wrap all elements in pages
            split_at = 'div.page-header'
            $(this).find(split_at).each ->
                $(this).add($(this).nextUntil(split_at)).wrapAll '<div class="ar_publish_page"/>'
                return

            # Move headers and footers out of the wrapping and assign
            # the top and bottom margins
            $(this).find('div.page-header').each ->
                baseheight = $(this).height()
                $(this).css
                    height: pxTomm(baseheight) + 'mm'
                    margin: 0
                    padding: pxTomm(mmTopx(dim.marginTop) - baseheight) + 'mm 0 0 0'
                $(this).parent().before this
                return

            $(this).find('div.page-break').each ->
                $(this).parent().after this
                return

            $(this).find('div.page-footer').each ->
                $(this).css
                    height: dim.marginBottom + 'mm'
                    margin: 0
                    padding: 0
                $(this).parent().after this
                return

            # First page may have a different margin to compensate for
            # first-page-footer.
            $(this).find('div.first-page-footer').each ->
                $(this).css
                    height: dim.firstMarginBottom + 'mm'
                    margin: 0
                    padding: 0
                $(this).parent().after this
                return

            # Page numbering
            pagenum = 1
            pagecntidx = 0
            $(this).find('.page-current-num,.page-total-count,div.page-break').each ->
                if $(this).hasClass('page-break')
                    if $(this).hasClass('restart-page-count')
                        pagenum = 1
                        pagecntidx += 1
                    else
                        pagenum = parseInt($(this).attr('data-pagenum')) + 1
                else if $(this).hasClass('page-current-num')
                    $(this).html pagenum
                else
                    $(this).html pagecounts[pagecntidx]
                return

            return

        # Set the page width and height, and the margins here, afterwards,
        # because in the loop above, some adjustments can be made.
        $('#margin-top').val dim.marginTop
        $('#margin-right').val dim.marginRight
        $('#margin-bottom').val dim.marginBottom
        $('#margin-left').val dim.marginLeft
        layout_style = '@page { size:    ' + dim.size + ' ' + orientation + ' !important; margin: 0mm ' + dim.marginRight + 'mm 0mm ' + dim.marginLeft + 'mm !important;' + '}'
        $('#layout-style').html layout_style
        $('#ar_publish_container').css
            width: dim.width + 'mm'
            padding: '0mm ' + dim.marginRight + 'mm 0mm ' + dim.marginLeft + 'mm '
        $('#ar_publish_header').css 'margin', '0mm -' + dim.marginRight + 'mm 0mm -' + dim.marginLeft + 'mm'
        $('div.ar_publish_body').css
            width: dim.width + 'mm'
            'max-width': dim.width + 'mm'
            'min-width': dim.width + 'mm'
        # Remove manual page breaks
        $('.manual-page-break').remove()
        return

    that.load = ->
        # Format and layout on first load.    see reloadReport() below.
        # Doing this manually here prevents immediately re-rendering template.
        load_barcodes()
        load_layout()
        #                window.bika.lims.RangeGraph.load();
        convert_svgs()
        # Store referrer in cookie in case it is lost due to a page reload
        cookiename = 'ar.publish.view.referrer'
        backurl = document.referrer
        if backurl
            createCookie cookiename, backurl
        else
            backurl = readCookie(cookiename)
            # Fallback to portal_url instead of staying inside publish.
            if !backurl
                backurl = portal_url
        # Smooth scroll to content
        $('#ar_publish_container #ar_publish_summary a[href^="#"]').click (e) ->
            e.preventDefault()
            anchor = $(this).attr('href')
            offset = $(anchor).first().offset().top - 20
            $('html,body').animate { scrollTop: offset }, 'fast'
            return

        $('#sel_format').change (e) ->
            reloadReport()
            return

        $('#landscape').click (e) ->
            # get the checkbox value
            landscape = if $('#landscape').is(':checked') then 1 else 0
            $('body').toggleClass 'landscape', landscape
            # reverse the dimensions of all layouts
            for key of papersizes
                papersizes[key]['dimensions'].reverse()
            reloadReport()
            return

        $('#qcvisible').click (e) ->
            reloadReport()
            return

        $('#hvisible').click (e) ->
            reloadReport()
            return

        $('#sel_layout').change (e) ->
            $('body').removeClass $('body').attr('data-layout')
            $('body').attr 'data-layout', $(this).val()
            $('body').addClass $(this).val()
            reloadReport()
            return

        $('#publish_button').click (e) ->
            url = window.location.href
            qcvisible = if $('#qcvisible').is(':checked') then 1 else 0
            hvisible = if $('#hvisible').is(':checked') then 1 else 0
            template = $('#sel_format').val()
            $('#ar_publish_container').animate { opacity: 0.4 }, 'slow'
            count = $('#ar_publish_container #report .ar_publish_body').length
            $('#ar_publish_container #report .ar_publish_body').each ->
                rephtml = $(this).clone().wrap('<div>').parent().html()
                coanr = $(rephtml).find('[name=coanr]').val();
                repstyle = $('#report-style').clone().wrap('<div>').parent().html()
                repstyle += $('#layout-style').clone().wrap('<div>').parent().html()
                repstyle += $('#layout-print').clone().wrap('<div>').parent().html()
                $.ajax(
                    url: url
                    type: 'POST'
                    async: false
                    data:
                        publish: 1
                        id: $(this).attr('id')
                        uid: $(this).attr('uid')
                        html: rephtml
                        template: template
                        qcvisible: qcvisible
                        hvisible: hvisible
                        style: repstyle
                        coanr: coanr
                ).always ->
                    if !--count
                        location.href = backurl
                    return

                return

            return

        $('#cancel_button').click (e) ->
            location.href = backurl
            return

        invalidbackurl = window.portal_url + '/++resource++bika.lims.images/report_invalid_back.png'
        $('.ar-invalid').css 'background', 'url("' + invalidbackurl + '") repeat scroll #ffffff'
        provisbackurl = window.portal_url + '/++resource++bika.lims.images/report_provisional_back.png'
        $('.ar-provisional').css 'background', 'url("' + provisbackurl + '") repeat scroll #ffffff'
        $('#sel_format_info').click (e) ->
            e.preventDefault()
            $('#sel_format_info_pane').toggle()
            return

        $('#margin-top').change (e) ->
            applyMargin $(this), 0
            reloadReport()
            return

        $('#margin-right').change (e) ->
            applyMargin $(this), 1
            reloadReport()
            return

        $('#margin-bottom').change (e) ->
            applyMargin $(this), 2
            reloadReport()
            return

        $('#margin-left').change (e) ->
            applyMargin $(this), 3
            reloadReport()
            return

        return

    return

