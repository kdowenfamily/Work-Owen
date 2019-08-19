" Colors
colorscheme pablo
syntax enable

" Tab stops
set tabstop=4
set shiftwidth=4
set softtabstop=4
set expandtab

" Indenting for File Types
filetype indent on

" When using <tab> in edlin, show all options
set wildmenu

" Searching
set incsearch           " search as characters are entered
set hlsearch            " highlight matches
nnoremap ,<space> :nohlsearch<CR>

" Folding
set foldenable
set foldmethod=indent
set foldlevelstart=0
set foldnestmax=5
nnoremap <space> za
