! Reads the assignment csv file for each rank
program read_assignments

    implicit none
    integer, dimension(48, 4248) :: assignments
    !integer, dimension(num_cpus, ncell_max), allocatable :: assignments

    ! open 'Mappings/original.csv' for reading
    open (unit=10, file='Mappings/original.csv', status='old')

    ! read in the assignments
    read (10, *) assignments

    ! write it out to console to check
    write (*,*) assignments

end program read_assignments

