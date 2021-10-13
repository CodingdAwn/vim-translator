" ============================================================================
" FileName: audio.vim
" Author: dawn <gaoxifengfordawn@gmail.com>
" GitHub: https://github.com/CodingdAwn
" ============================================================================

function! translator#audio#jobstart(cmd) 
  let g:translator_status = 'speaking'
  if has('nvim')
    let callback = {}
    call jobstart(a:cmd, callback)
  else
    let callback = {}
    call job_start(a:cmd, callback)
  endif
endfunction
