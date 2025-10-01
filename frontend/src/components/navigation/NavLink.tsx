import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useUploadStore } from '../../store/uploadStore';

interface NavLinkProps {
  to: string;
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const NavLink: React.FC<NavLinkProps> = ({ to, children, className, onClick }) => {
  const navigate = useNavigate();
  const { clearFiles } = useUploadStore();

  const handleClick = (e: React.MouseEvent) => {
    // 如果点击的是智能构图链接，先清理状态
    if (to === '/upload') {
      e.preventDefault();
      clearFiles();
      navigate('/upload');
    }
    
    // 执行自定义的onClick回调
    if (onClick) {
      onClick();
    }
  };

  return (
    <Link 
      to={to} 
      className={className}
      onClick={handleClick}
    >
      {children}
    </Link>
  );
};

export default NavLink;
