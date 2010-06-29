<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="stylesheet" type="text/css" href="index.css" />
    <title>Computer Science Club Mirror</title>
  </head>
  
  <body>
    <div id="logo">
      <a href="/"><img src="/include/header.png" alt="Computer Science Club Mirror - The University of Waterloo - Funded by MEF" title="Computer Science Club Mirror - The University of Waterloo - Funded by MEF" /></a>
    </div>
    
    <div id="listing">
      <table>
        <tr><th>Directory</th><th>Project Site</th><th>Size</th></tr>
	
        % for dir in directories:
        <tr>
          <td>
            ${h.link_to(dir['dir']+'/', '/'+dir['dir']+'/')}
          </td>

          <td>
	    % if 'site' in dir:
            ${h.link_to(dir['site'], dir['url'])}
	    % endif
          </td>

          <td>${dir['size'] | h}</td>
        </tr>

	% endfor \
	
	<tr class="total">
	  <td>Total</td>
	  <td></td>
	  <td>${total_size}</td>
	</tr>
      </table>
    </div>

    <div id="footer">
      <p>This service is run by the <a href="http://csclub.uwaterloo.ca/">Computer Science Club of the University of Waterloo</a>.<br />It is made possible by funding from the <a href="http://www.student.math.uwaterloo.ca/~mefcom/home">Mathematics Endowment Fund</a><br />and support from the <a href="http://www.cs.uwaterloo.ca">David R. Cheriton School of Computer Science</a>.</p>
    </div>
  </body>
</html>
