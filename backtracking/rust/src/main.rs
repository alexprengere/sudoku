use rustc_hash::FxHashMap;
use rustc_hash::FxHashSet;
use std::env;
use std::fs::File;
use std::io;
use std::io::prelude::*;
use std::iter::FromIterator;
use std::path::Path;

struct Sudoku {
    data: [u8; 81],
}

// The output is wrapped in a Result to allow matching on errors
// Returns an Iterator to the Reader of the lines of the file.
fn read_lines<P>(filename: P) -> io::Result<io::Lines<io::BufReader<File>>>
where
    P: AsRef<Path>,
{
    let file = File::open(filename)?;
    Ok(io::BufReader::new(file).lines())
}

impl Sudoku {
    fn new(filename: &str) -> Sudoku {
        let mut data = [0u8; 81];

        if let Ok(lines) = read_lines(filename) {
            let mut i = 0;
            for (ln, line_) in lines.enumerate() {
                if let Ok(line) = line_ {
                    if ln == 3 || ln == 7 {
                        continue;
                    }
                    let mut j = 0;
                    for (cn, c) in line.chars().enumerate() {
                        if cn == 3 || cn == 7 {
                            continue;
                        }
                        if c != '.' {
                            data[i * 9 + j] = c.to_digit(10).unwrap() as u8;
                        }
                        j += 1;
                    }
                    i += 1;
                }
            }
        }
        Sudoku { data }
    }

    fn copy(&self) -> Sudoku {
        Sudoku {
            data: self.data,
        }
    }

    fn show(&self) {
        for k in 0..81 {
            let i = k / 9;
            let j = k % 9;
            let n = self.data[k];
            if n == 0 {
                print!(".");
            } else {
                print!("{}", n);
            }
            if j == 2 || j == 5 {
                print!(" ");
            } else if j == 8 {
                println!();
                if i == 2 || i == 5 {
                    println!();
                }
            }
        }
    }

    fn get_neighbor_indices(k: u8) -> FxHashSet<u8> {
        let i = k / 9;
        let j = k % 9;
        let mut indices = FxHashSet::default();

        for dj in 0..9 {
            if dj != j {
                indices.insert(i * 9 + dj);
            }
        }

        for di in 0..9 {
            if di != i {
                indices.insert(di * 9 + j);
            }
        }

        let li = (i / 3) * 3;
        let lj = (j / 3) * 3;
        for di in li..li + 3 {
            for dj in lj..lj + 3 {
                if di != i || dj != j {
                    indices.insert(di * 9 + dj);
                }
            }
        }

        indices
    }

    fn solve(&mut self) {
        let mut possibilities = FxHashMap::<u8, u16>::default();
        for k in 0..81 {
            if self.data[k as usize] == 0 {
                possibilities.insert(k, 0b1_1111_1111); // All digits possible
            }
        }
        let unknown: FxHashSet<u8> = possibilities.keys().copied().collect();

        let mut neighbors: FxHashMap<u8, FxHashSet<u8>> = FxHashMap::default();
        for k in 0..81 {
            let indices = Sudoku::get_neighbor_indices(k);
            neighbors.insert(k, indices.intersection(&unknown).copied().collect());
        }

        for k in 0..81 {
            let n = self.data[k as usize];
            if n != 0 {
                let mask = 1 << (n - 1);
                for &di_dj in &neighbors[&k] {
                    if possibilities[&di_dj] & mask != 0 {
                        if let Some(set) = possibilities.get_mut(&di_dj) {
                            *set &= !mask; // Remove digit n from possibilities
                        }
                    }
                }
            }
        }

        let mut stack = vec![(self.copy(), possibilities)];
        while let Some((mut state, mut poss)) = stack.pop() {
            let mut stuck = false;
            let mut backtrack = false;

            while !stuck && !backtrack {
                stuck = true;
                let poss_keys: Vec<u8> = poss.keys().copied().collect();
                for &k in &poss_keys {
                    let set = poss[&k];
                    if set == 0 {
                        backtrack = true;
                        break;
                    } else if set.count_ones() == 1 {
                        let n = set.trailing_zeros() as u8 + 1;
                        state.data[k as usize] = n;
                        poss.remove(&k);
                        let mask = 1 << (n - 1);
                        for &di_dj in &neighbors[&k] {
                            if poss.contains_key(&di_dj) && (poss[&di_dj] & mask) != 0 {
                                if let Some(set_di_dj) = poss.get_mut(&di_dj) {
                                    *set_di_dj &= !mask;
                                    stuck = false;
                                }
                            }
                        }
                    }
                }
            }

            if backtrack {
                continue;
            }

            if poss.is_empty() {
                self.data = state.data;
                return;
            }

            let mut min_len = 10; // max cannot exceed 9
            let mut min_k = 0;

            for (&k, &set) in &poss {
                let len = set.count_ones();
                if (len, k) < (min_len, min_k) {
                    min_len = len;
                    min_k = k;
                }
            }

            for n in 1..10 {
                let mask = 1 << (n - 1);
                if (poss[&min_k] & mask) == 0 {
                    continue;
                }
                let mut new_state = state.copy();
                let mut new_poss = poss.clone();
                new_state.data[min_k as usize] = n;
                new_poss.remove(&min_k);
                for &di_dj in &neighbors[&min_k] {
                    if new_poss.contains_key(&di_dj) && (new_poss[&di_dj] & mask) != 0 {
                        if let Some(set_di_dj) = new_poss.get_mut(&di_dj) {
                            *set_di_dj &= !mask;
                        }
                    }
                }
                stack.push((new_state, new_poss));
            }
        }

        panic!("Not solvable");
    }

    fn get_lines(&self) -> Vec<Vec<u8>> {
        let mut lines = Vec::new();
        for i in 0..9 {
            let mut line = Vec::new();
            for j in 0..9 {
                line.push(self.data[i * 9 + j]);
            }
            lines.push(line);
        }
        lines
    }

    fn get_columns(&self) -> Vec<Vec<u8>> {
        let mut columns = Vec::new();
        for j in 0..9 {
            let mut column = Vec::new();
            for i in 0..9 {
                column.push(self.data[i * 9 + j]);
            }
            columns.push(column);
        }
        columns
    }

    fn get_squares(&self) -> Vec<Vec<u8>> {
        let mut squares = Vec::new();
        for li in [0, 3, 6].iter() {
            for lj in [0, 3, 6].iter() {
                let mut square = Vec::new();
                for i in *li..*li + 3 {
                    for j in *lj..*lj + 3 {
                        square.push(self.data[i * 9 + j]);
                    }
                }
                squares.push(square);
            }
        }
        squares
    }

    fn is_solved(&self) -> bool {
        let full: FxHashSet<u8> = FxHashSet::from_iter(1..10);

        let parts = [self.get_lines(), self.get_columns(), self.get_squares()];

        for numbers in parts.iter().flat_map(|it| it.clone()) {
            let h: FxHashSet<u8> = FxHashSet::from_iter(numbers);
            if h != full {
                return false;
            }
        }
        true
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let mut sudoku = Sudoku::new(&args[1]);
    sudoku.solve();
    sudoku.show();
    debug_assert!(sudoku.is_solved());
}
