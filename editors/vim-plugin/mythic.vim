" mythic.vim -- Mythic Agent integration for Vim/Neovim (Slice 38)
"
" Sends prompts (or buffer contents) to `mythic run` and shows the result
" in a scratch window. Requires the `mythic` CLI on $PATH.
"
" Install: copy this file to ~/.vim/plugin/mythic.vim
"          (Neovim: ~/.config/nvim/plugin/mythic.vim)
"
" Commands:
"   :MythicRun {prompt}        Run a one-shot task, show result in scratch
"   :MythicRunBuffer [prompt]  Send current buffer (+ optional prompt)
"   :MythicRunSelection        Send the visual selection (mapped to <Leader>mr)
"
" Options:
"   let g:mythic_command = 'mythic'        " CLI binary (default 'mythic')
"   let g:mythic_workspace = ''            " default workspace (default: cwd)
"   let g:mythic_permission = 'read-only'  " permission mode for runs

if exists('g:loaded_mythic') || &compatible
  finish
endif
let g:loaded_mythic = 1

function! s:MythicCmd() abort
  return get(g:, 'mythic_command', 'mythic')
endfunction

function! s:OpenScratch(title) abort
  botright new
  setlocal buftype=nofile bufhidden=wipe noswapfile nobuflisted
  setlocal filetype=markdown
  execute 'file ' . a:title
  return bufnr('%')
endfunction

function! s:RunMythic(prompt, input) abort
  let l:workspace = get(g:, 'mythic_workspace', '')
  let l:cmd = s:MythicCmd() . ' run --format plain'
  if !empty(l:workspace)
    let l:cmd .= ' --workspace ' . shellescape(l:workspace)
  endif
  let l:permission = get(g:, 'mythic_permission', 'read-only')
  if !empty(l:permission)
    let l:cmd .= ' --permission ' . shellescape(l:permission)
  endif
  let l:cmd .= ' ' . shellescape(a:prompt)
  echo 'Mythic is working...'
  let l:output = system(l:cmd, a:input)
  if v:shell_error
    echohl ErrorMsg | echomsg 'mythic run failed (exit ' . v:shell_error . ')' | echohl None
    return
  endif
  let l:buf = s:OpenScratch('[Mythic] ' . a:prompt[:47])
  call setbufline(l:buf, 1, split(l:output, "\n"))
  normal! gg
  echo 'Mythic finished.'
endfunction

command! -nargs=+ -complete=file MythicRun
      \ call s:RunMythic(<q-args>, '')

command! -nargs=? -complete=file MythicRunBuffer
      \ call s:RunMythic(empty(<q-args>) ? 'Review and improve this file.' : <q-args>,
      \                  join(getline(1, '$'), "\n"))

function! s:RunMythicSelection() range abort
  let l:lines = getline(a:firstline, a:lastline)
  call s:RunMythic('Explain or improve the following code:', join(l:lines, "\n"))
endfunction

xnoremap <silent> <Leader>mr :<C-u>call <SID>RunMythicSelection()<CR>
nnoremap <silent> <Leader>mr :MythicRunBuffer<CR>
